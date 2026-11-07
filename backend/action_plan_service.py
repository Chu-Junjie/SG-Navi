"""Task 19: action-first service using Task 16 contract and Task 17 reviewed sources.

No source text, contact, legal outcome or filing deadline is constructed here.
The same confirmed context and its revision must be revalidated by the client
when displaying a reply. This service never saves raw descriptions or facts.
"""
from jsonschema import ValidationError

from backend.scenario_understanding import (
    interpret_scenario, next_decisive_question,
)
from rag.action_evidence import (
    ActionEvidenceUnavailable, load_action_package, select_action_plan,
)
from shared.validate_action_plan import context_revision, validate_action_plan

VERSION = "1.0"
OUTSIDE = (
    "This situation is outside the currently supported assistance scope. "
    "Check the relevant institution's official guidance."
)


def envelope(request_id, state, reason, message, *, context=None, question=None, plan=None):
    revision = context_revision(context) if context is not None and state != "CONFIRM" else None
    result = {
        "action_plan_version": VERSION,
        "request_id": request_id,
        "state": state,
        "reason": reason,
        "message": message,
        "context": context,
        "revision": revision,
        "question": question,
        "plan": plan,
    }
    validate_action_plan(result, "response")
    return result


def _out_of_scope(facts):
    return (
        facts.get("purchase_purpose") == "business"
        or facts.get("merchant_location") == "outside_singapore"
        or facts.get("supplier_registered_in_sg") is False
        or facts.get("premises_type") in ("commercial", "industrial")
    )


def _choice(field, prompt, reason, values):
    return {
        "id": "decide_" + field, "field": field,
        "prompt": prompt, "reason": reason,
        "options": [{"value": value, "label": label} for value, label in values],
    }


def _extra_question(context):
    """Ask only about source-profile decisive facts; never generic eligibility."""
    f = context["facts"]
    if context["case_type"] == "consumer_complaint":
        # The source-reviewed restaurant/goods preparation contacts are local.
        if ("merchant_location" not in f and
                context["issue_subtype"] != "unspecified"):
            return _choice(
                "merchant_location", "Was the purchase or bill in Singapore?",
                "The official local assistance route depends on where the transaction took place.",
                [("singapore", "Singapore"),
                 ("outside_singapore", "Outside Singapore"),
                 ("unknown", "Not sure")],
            )
        # This question is needed only for a complaint intake *after* an
        # attempted resolution and when the personal/local context is clear.
        if (context["issue_subtype"] in ("restaurant_overcharge", "duplicate_charge", "unclear_charge")
                and context["goal"] in ("complain", "seek_refund", "understand_options")
                and f.get("resolution_attempted") is True
                and f.get("merchant_location") == "singapore"
                and f.get("purchase_purpose") == "personal"
                and "consumer_context" not in f):
            return _choice(
                "consumer_context", "Are you seeking help as a local consumer or a visitor?",
                "The reviewed complaint-contact profile distinguishes its service audience.",
                [("local_consumer", "Local consumer"),
                 ("visitor", "Visitor"),
                 ("unknown", "Not sure")],
            )
    else:
        if (context["issue_subtype"] in ("agent_conduct", "agency_agreement")
                and "dispute_with" not in f):
            return _choice(
                "dispute_with", "Is your concern with the landlord or estate agent?",
                "This determines which agency or dispute procedure should be explored.",
                [("landlord", "Landlord"), ("agent", "Estate agent"),
                 ("unknown", "Not sure")],
            )
    return None


def process_action_plan(request, *, repository=None, directory=None, now=None):
    """Process one validated request. No HTTP or API-side effects.

    Optional dependency injection supports isolated tests. Production always
    resolves Task 17's current package version, never a hardcoded fixture ID.
    """
    validate_action_plan(request, "request")
    request_id = request["request_id"]
    if request["operation"] == "interpret":
        candidate = interpret_scenario(request["description"])
        if candidate["status"] != "candidate":
            reason = ("ambiguous_scope" if candidate["status"] == "ambiguous_scope"
                      else "outside_scope" if candidate["status"] == "outside_scope"
                      else "insufficient_facts")
            message = {
                "ambiguous_scope": "More than one unrelated dispute is described. Select one issue to continue.",
                "outside_scope": OUTSIDE,
                "insufficient_facts": "Describe the disputed payment, purchase or rental deposit and what happened.",
            }[reason]
            result = envelope(request_id, "LIMITED", reason, message)
        else:
            result = envelope(
                request_id, "CONFIRM", "awaiting_confirmation",
                "Please confirm this understanding or correct the details before proceeding.",
                context=candidate["context"],
            )
        validate_action_plan(result, request=request)
        return result

    context = request["context"]
    f = context["facts"]
    if _out_of_scope(f):
        result = envelope(request_id, "LIMITED", "outside_scope", OUTSIDE, context=context)
    else:
        question = next_decisive_question(context)
        if question is None:
            question = _extra_question(context)
        if question is not None:
            result = envelope(
                request_id, "ASK", "missing_decisive_fact",
                "One detail may change the appropriate next step.",
                context=context, question=question,
            )
        else:
            try:
                options = {"directory": directory} if directory is not None else {}
                package, _, _, _ = load_action_package(**options)
                arguments = dict(expected_version=package["version"], **options)
                if repository is not None:
                    arguments["repository"] = repository
                if now is not None:
                    arguments["now"] = now
                plan = select_action_plan(context, **arguments)
                if plan is None:
                    result = envelope(
                        request_id, "LIMITED", "insufficient_facts",
                        "The confirmed details do not yet establish a reviewed next-step profile. "
                        "Check the disputed transaction or signed tenancy records and correct any "
                        "uncertain details before choosing a formal route.",
                        context=context,
                    )
                else:
                    result = envelope(
                        request_id, "READY", "verified_action",
                        "A reviewed preparation or assistance step is available. "
                        "This does not establish eligibility or guarantee an outcome.",
                        context=context, plan=plan,
                    )
            except (ActionEvidenceUnavailable, OSError, KeyError, ValueError, ValidationError):
                result = envelope(
                    request_id, "LIMITED", "source_unverified",
                    "The current evidence or contact could not be verified. "
                    "No source-backed action can be displayed; review the applicable official guidance.",
                    context=context,
                )
    validate_action_plan(result, request=request)
    return result
