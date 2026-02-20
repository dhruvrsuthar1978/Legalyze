from typing import Dict, List


_TEMPLATES: Dict[str, Dict] = {
    "mutual_nda": {
        "id": "mutual_nda",
        "name": "Mutual NDA",
        "description": "Two-way confidentiality agreement for sharing sensitive information.",
        "fields": [
            "party_1_name",
            "party_2_name",
            "effective_date",
            "term_months",
            "governing_law",
            "purpose",
            "additional_terms",
        ],
    },
    "service_agreement": {
        "id": "service_agreement",
        "name": "Service Agreement",
        "description": "Defines services, payment, delivery, and liability limits between client and provider.",
        "fields": [
            "party_1_name",
            "party_2_name",
            "effective_date",
            "term_months",
            "payment_terms",
            "scope_of_services",
            "governing_law",
            "additional_terms",
        ],
    },
    "employment_offer": {
        "id": "employment_offer",
        "name": "Employment Offer",
        "description": "Offer and basic employment terms balancing employer and employee obligations.",
        "fields": [
            "party_1_name",
            "party_2_name",
            "effective_date",
            "position_title",
            "base_salary",
            "termination_notice_days",
            "governing_law",
            "additional_terms",
        ],
    },
    "consulting_agreement": {
        "id": "consulting_agreement",
        "name": "Consulting Agreement",
        "description": "Independent consultant contract covering deliverables, payment, IP, and confidentiality.",
        "fields": [
            "party_1_name",
            "party_2_name",
            "effective_date",
            "term_months",
            "payment_terms",
            "deliverables",
            "governing_law",
            "additional_terms",
        ],
    },
}


def list_templates() -> List[Dict]:
    return list(_TEMPLATES.values())


def render_template_preview(template_id: str, data: Dict) -> Dict:
    template = _TEMPLATES.get(template_id)
    if not template:
        raise ValueError("Unknown template_id.")

    party_1 = data.get("party_1_name", "Party A")
    party_2 = data.get("party_2_name", "Party B")
    effective_date = data.get("effective_date", "Effective Date")
    term_months = data.get("term_months", "12")
    governing_law = data.get("governing_law", "Applicable Jurisdiction")
    payment_terms = data.get("payment_terms", "Mutually agreed written invoice terms.")
    purpose = data.get("purpose", "evaluating and discussing a potential business relationship")
    scope_of_services = data.get("scope_of_services", "Services listed in Annex A.")
    position_title = data.get("position_title", "Employee")
    base_salary = data.get("base_salary", "as agreed in writing")
    termination_notice_days = data.get("termination_notice_days", "30")
    deliverables = data.get("deliverables", "deliverables agreed in writing")
    additional_terms = data.get("additional_terms", "").strip()

    if template_id == "mutual_nda":
        body = f"""MUTUAL NON-DISCLOSURE AGREEMENT

This Mutual NDA is made effective on {effective_date} between {party_1} and {party_2}.

1. Purpose
The parties will share confidential information for {purpose}.

2. Confidential Information
Each party may disclose non-public business, technical, financial, or legal information.

3. Mutual Obligations
Each party will:
- use confidential information only for the stated purpose;
- protect it with reasonable safeguards;
- not disclose it to third parties except advisors under confidentiality duties.

4. Exclusions
Information is not confidential if it is publicly available, independently developed, or lawfully received from another source.

5. Term and Survival
This agreement remains active for {term_months} months. Confidentiality obligations survive for 3 years after disclosure unless law requires longer.

6. Fairness and Remedies
Both parties have equal confidentiality duties and equal rights to seek injunctive relief for unauthorized disclosure.

7. Governing Law
This agreement is governed by {governing_law}.
"""
    elif template_id == "service_agreement":
        body = f"""SERVICE AGREEMENT

This Service Agreement is effective on {effective_date} between {party_1} (Client) and {party_2} (Provider).

1. Services
Provider will perform: {scope_of_services}

2. Payment Terms
Client will pay according to: {payment_terms}
Both parties agree invoices and deliverables must be reasonably documented.

3. Term
The agreement continues for {term_months} months unless terminated earlier under this agreement.

4. Performance and Cooperation
Provider will deliver services with reasonable skill and care.
Client will provide timely access, approvals, and information needed for delivery.

5. Liability Allocation
Each party is responsible for direct losses caused by its breach.
Neither party is liable for indirect or consequential losses, except for confidentiality or IP breaches.

6. Termination
Either party may terminate for material breach not cured within 15 days after written notice.

7. Governing Law
This agreement is governed by {governing_law}.
"""
    elif template_id == "employment_offer":
        body = f"""EMPLOYMENT OFFER TERMS

This offer is made on {effective_date} by {party_1} (Employer) to {party_2} (Employee) for the role of {position_title}.

1. Compensation
Base salary: {base_salary}. Any bonus or incentive program will be documented in writing.

2. Duties
Employee will perform duties reasonably associated with the role and follow lawful employer policies.
Employer will provide resources and support reasonably required for role performance.

3. Confidentiality and IP
Employee agrees to protect confidential information.
IP created in scope of employment belongs to Employer, while Employee retains pre-existing IP.

4. Fair Workplace Commitments
Employer commits to equal treatment, lawful working conditions, and timely payment.
Employee commits to professionalism, compliance, and good-faith performance.

5. Termination Notice
Either party may terminate employment with {termination_notice_days} days notice unless terminated for cause under applicable law.

6. Governing Law
This employment relationship is governed by {governing_law}.
"""
    else:
        body = f"""CONSULTING AGREEMENT

This Consulting Agreement is effective on {effective_date} between {party_1} (Client) and {party_2} (Consultant).

1. Deliverables
Consultant will provide: {deliverables}

2. Payment
Client will pay according to: {payment_terms}

3. Term
The agreement remains in effect for {term_months} months unless ended earlier under this agreement.

4. Independent Contractor
Consultant acts as an independent contractor and not as an employee or partner of Client.

5. IP and Confidentiality
Project deliverables prepared for Client are assigned to Client upon full payment.
Both parties must protect each other's confidential information.

6. Fair Risk Allocation
Each party is liable for its own breaches. Liability is limited to reasonably foreseeable direct damages.

7. Governing Law
This agreement is governed by {governing_law}.
"""

    if additional_terms:
        body = f"{body}\nAdditional Terms:\n{additional_terms}\n"

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "preview_text": body.strip(),
        "estimated_pages": max(1, len(body.split()) // 300),
        "fields_used": {k: v for k, v in data.items() if v not in [None, ""]},
    }
