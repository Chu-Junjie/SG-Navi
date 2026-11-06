"""Editorial search tags, not legal rules, thresholds or official quotations.

Each row describes an existing rule mapping; actual Evidence IDs always come
from the current validated corpus. Words select research topics, not facts.
"""

LANDLORD = ("landlord",)
CONTRACT = ("agent_contract",)
CONDUCT = ("agent_conduct",)
CONSUMER = ("consumer",)
COURT = LANDLORD + CONSUMER

# rule -> (allowed research channels, search words, relevant confirmed fields)
TOPICS = {
    "SCT_RESIDENTIAL_SCOPE": (LANDLORD, "landlord deposit rent rental tenancy tenant residential duration lease", ("dispute_with", "premises_type", "tenancy_duration_months")),
    "SCT_CLAIM_AMOUNT": (COURT, "amount ceiling limit money claim", ("claim_amount_sgd",)),
    "SCT_EVENT_DATE": (COURT, "deadline time date limitation event", ("relevant_event_date",)),
    "SCT_RESPONDENT_SERVICE": (COURT, "respondent location singapore serve service", ("respondent_in_singapore",)),
    "SCT_GOODS_SERVICES_SCOPE": (CONSUMER, "goods service product faulty defective refund purchase seller consumer", ("purchase_type", "problem_type")),
    "SCT_FILING_PORTAL": (COURT, "file filing portal application online", ()),
    "SCT_DOCUMENTS": (COURT, "document record agreement receipt invoice message translation evidence", ("documents_available",)),
    "SCT_FILING_FEES": (COURT, "filing fee cost payment", ()),
    "SCT_SERVICE_DEADLINE": (COURT, "serve service notice consultation", ()),
    "SCT_PROOF_OF_SERVICE": (COURT, "proof serve service declaration", ()),
    "CEA_AGENCY_AGREEMENT": (CONTRACT, "agency agreement contract commission agent", ("agency_agreement_signed",)),
    "CEA_AGREEMENT_DISPUTE": (CONTRACT, "agency agreement contract term commission", ("agency_agreement_signed",)),
    "CEA_MEDIATION": (CONTRACT, "mediation mediate settlement centre", ("resolution_attempted",)),
    "CEA_ARBITRATION": (CONTRACT, "arbitration arbitrator binding", ()),
    "CEA_CENTRE_INDEPENDENCE": (CONTRACT, "independent centre oversee", ()),
    "CEA_CONDUCT_COMPLAINT": (CONDUCT, "conduct misconduct unlicensed complaint complain agent", ()),
    "CEA_COMPLAINT_PRIVACY": (CONDUCT, "privacy anonymous anonymity disclose disclosure", ()),
    "CEA_COMPLAINT_SUBMISSION": (CONDUCT, "document record singpass submit submission complaint", ("documents_available",)),
    "CEA_COMPLAINT_RECORDS": (CONDUCT, "chronology timeline transaction record", ()),
    "CASE_PERSONAL_PURPOSE": (CONSUMER, "consumer personal domestic household purchase faulty defective refund", ("purchase_purpose",)),
    "CASE_SINGAPORE_SUPPLIER": (CONSUMER, "supplier seller merchant singapore registered company", ("supplier_registered_in_sg", "supplier_location")),
    "CASE_DOCUMENTS": (CONSUMER, "document receipt invoice purchase proof contract record", ("documents_available",)),
    "CASE_PROCESS_FEES": (CONSUMER, "fee membership consultation letter cost process", ("resolution_attempted",)),
}

ALIASES = {
    "documents": "document", "records": "record", "receipts": "receipt",
    "invoices": "invoice", "fees": "fee", "costs": "cost",
    "goods": "goods", "services": "service", "products": "product",
    "deposits": "deposit", "landlords": "landlord", "agents": "agent",
    "agreements": "agreement", "complaints": "complaint", "deadlines": "deadline",
    "sellers": "seller", "registered": "registered", "refunds": "refund",
    "refunding": "refund", "filing": "filing", "tenancies": "tenancy",
}

# With no optional query, only these contextual topics are seeded. More
# specific topics still require confirmed fields or matching query terms.
CORE = {
    "landlord": {"SCT_RESIDENTIAL_SCOPE"},
    "agent_contract": {"CEA_AGENCY_AGREEMENT", "CEA_AGREEMENT_DISPUTE"},
    "agent_conduct": {"CEA_CONDUCT_COMPLAINT"},
    "consumer": {"CASE_PERSONAL_PURPOSE", "SCT_GOODS_SERVICES_SCOPE"},
}
