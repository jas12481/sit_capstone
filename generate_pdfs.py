import os, io, random, hashlib
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

# ── COLOUR PALETTE (BLACK & WHITE PROFESSIONAL) ───────────────────────────────
BLACK      = colors.HexColor('#000000')
DARK_GREY  = colors.HexColor('#1A1A1A')
MID_GREY   = colors.HexColor('#555555')
LIGHT_GREY = colors.HexColor('#AAAAAA')
RULE_GREY  = colors.HexColor('#CCCCCC')
BG_GREY    = colors.HexColor('#F5F5F5')
WHITE      = colors.white

def make_styles():
    return {
        'co':       ParagraphStyle('co',      fontSize=16, fontName='Helvetica-Bold', textColor=BLACK,     alignment=TA_CENTER, spaceAfter=4),
        'co_sub':   ParagraphStyle('co_sub',  fontSize=8,  fontName='Helvetica',      textColor=MID_GREY,  alignment=TA_CENTER, spaceAfter=2),
        'doc_title':ParagraphStyle('title',   fontSize=12, fontName='Helvetica-Bold', textColor=BLACK,     alignment=TA_CENTER, spaceBefore=6, spaceAfter=4),
        'doc_sub':  ParagraphStyle('doc_sub', fontSize=9,  fontName='Helvetica',      textColor=MID_GREY,  alignment=TA_CENTER, spaceAfter=6),
        'sec':      ParagraphStyle('sec',     fontSize=10, fontName='Helvetica-Bold', textColor=BLACK,     spaceBefore=12, spaceAfter=5),
        'subsec':   ParagraphStyle('subsec',  fontSize=9.5,fontName='Helvetica-Bold', textColor=DARK_GREY, spaceBefore=7,  spaceAfter=3),
        'body':     ParagraphStyle('body',    fontSize=9,  leading=14.5, spaceAfter=4, alignment=TA_JUSTIFY, textColor=DARK_GREY),
        'clause':   ParagraphStyle('clause',  fontSize=9,  leading=14.5, spaceAfter=3, leftIndent=10, alignment=TA_JUSTIFY, textColor=DARK_GREY),
        'sub':      ParagraphStyle('sub',     fontSize=9,  leading=14.5, spaceAfter=3, leftIndent=22, alignment=TA_JUSTIFY, textColor=DARK_GREY),
        'footer':   ParagraphStyle('footer',  fontSize=7.5,textColor=MID_GREY, alignment=TA_CENTER, spaceBefore=2),
        'lbl':      ParagraphStyle('lbl',     fontSize=8.5,fontName='Helvetica-Bold', textColor=BLACK),
        'val':      ParagraphStyle('val',     fontSize=8.5,textColor=DARK_GREY),
    }

def rng_for(pid):
    return random.Random(int(hashlib.md5(pid.encode()).hexdigest(), 16))

def rand_dob(rng):
    return date(rng.randint(1958, 1992), rng.randint(1, 12), rng.randint(1, 28))

def rand_nric(rng):
    d = ''.join(str(rng.randint(0, 9)) for _ in range(7))
    return f"S{d}{rng.choice('ABCDEFGHIJZ')}"

def mask(n): return f"S****{n[-4:]}"

def rand_addr(rng):
    e = rng.choice(['Tampines','Jurong West','Woodlands','Bedok','Ang Mo Kio',
                    'Toa Payoh','Bishan','Clementi','Punggol','Sengkang',
                    'Buona Vista','Pasir Ris','Yishun','Hougang','Serangoon'])
    return f"Blk {rng.randint(1,650)} {e} Street {rng.randint(1,42)} #{rng.randint(1,22):02d}-{rng.randint(1,350):03d} Singapore {rng.randint(100000,829999)}"

def rand_occ(rng):
    return rng.choice(['Software Engineer','Accountant','Teacher','Registered Nurse',
        'Business Analyst','Marketing Manager','Civil Servant','Medical Doctor',
        'Lawyer','Architect','Financial Analyst','Operations Manager',
        'Logistics Coordinator','Pharmacist','Mechanical Engineer','HR Manager',
        'Project Manager','Quantity Surveyor','Data Analyst','IT Consultant'])

BENE_NAMES = ['Tan Wei Ling','Lim Ah Seng','Wong Mei Fen','Lee Boon Kiat','Ng Swee Huat',
    'Priya d/o Rajan','Ahmad Bin Yusof','Siti Binte Hamid','Goh Choon Keng',
    'Chua Pei Shan','Ravi s/o Krishnan','Zainab Binte Omar','Ong Siew Lian',
    'Mohd Fadzil Bin Razali','Leong Mei Kuen','Jayakumar s/o Pillai',
    'Tan Boon Keng','Lim Swee Ling','Noor Aisyah Binte Hamid','Selvam s/o Raju']
RELS = ['Spouse','Child','Parent','Sibling']

# ── PRODUCT-SPECIFIC DIFFERENTIATORS ─────────────────────────────────────────
PRODUCT_DESCRIPTIONS = {
    # LIFE
    'AIA LifeGuard Essential':   ('Pure term life coverage for young adults seeking affordable protection. Provides a straightforward death benefit with no investment component.', '90 days', 'Term to age 65', 'None'),
    'AIA LifeGuard Plus':        ('Term life coverage with an enhanced accidental death multiplier of 150% of sum assured, providing additional protection for accidental fatalities.', '90 days', 'Term to age 65', '150% on accidental death'),
    'AIA LifeGuard Premier':     ('Premium term life plan with a 200% accidental death multiplier and TPD coverage to age 70, designed for high-income professionals.', '90 days', 'Term to age 70', '200% on accidental death'),
    'AIA SecureLife 300':        ('Family-oriented life plan covering death and TPD to age 65, with optional family rider for spouse and children.', '90 days', 'TPD to age 65', 'Family rider available'),
    'AIA SecureLife 600':        ('High-coverage life plan with death and TPD benefit to age 70 and premium waiver on TPD diagnosis.', '90 days', 'TPD to age 70', 'Premium waiver on TPD'),
    'AIA SecureLife Platinum':   ('Ultra-high-coverage life plan for high-net-worth individuals, with TPD to age 75 and enhanced accidental death benefit.', '90 days', 'TPD to age 75', 'Enhanced accidental death'),
    'AIA WholeCover Basic':      ('Whole of life plan with guaranteed cash value accumulation, providing lifelong coverage and a savings component.', '90 days', 'Whole of life', 'Guaranteed cash value'),
    'AIA WholeCover Premier':    ('Premium whole of life plan with enhanced cash value and investment-linked returns, for long-term wealth accumulation.', '90 days', 'Whole of life', 'Enhanced cash value'),
    'AIA FamilyShield Income':   ('Life plan designed for sole breadwinners, offering an optional monthly income payout to dependants upon the death of the insured.', '90 days', 'Term to age 65', 'Monthly income payout option'),
    'AIA MortgageGuard':         ('Decreasing term life plan designed to match an outstanding mortgage loan balance, protecting homeowners and their families.', '90 days', 'Matches loan term', 'Decreasing sum assured'),
    'AIA SeniorGuard 65':        ('Simplified underwriting life plan for applicants aged 50 to 70, with no medical examination required.', '90 days', 'Term to age 80', 'No medical exam required'),
    'AIA BusinessGuard Term':    ('Key person life insurance for business owners, providing a lump sum to the business upon the death or TPD of a key individual.', '90 days', 'Term to age 65', 'Key person business coverage'),
    'AIA EndowSave 20':          ('20-year endowment plan combining life protection with disciplined savings, with a guaranteed maturity benefit at the end of the term.', '90 days', '20-year term', 'Guaranteed maturity benefit'),
    'AIA EndowSave 25':          ('25-year endowment plan for retirement planning, with guaranteed maturity benefit and enhanced cash value accumulation.', '90 days', '25-year term', 'Retirement-focused endowment'),
    'AIA ConvertTerm Plus':      ('Convertible term life plan allowing conversion to a whole life or endowment plan without medical underwriting at any time during the policy term.', '90 days', 'Term to age 65', 'Conversion privilege without underwriting'),
    # HEALTH
    'AIA MediShield Basic':      ('Essential hospitalisation plan providing coverage for Ward B2/C in restructured hospitals, integrated with MediShield Life.', '30 days', 'Annual renewable', 'Ward B2/C coverage'),
    'AIA MediShield Standard':   ('Standard hospitalisation plan covering Ward B1 in restructured hospitals and day surgery, with outpatient surgical benefits.', '30 days', 'Annual renewable', 'Ward B1 coverage'),
    'AIA MediShield Gold':       ('Mid-tier hospitalisation plan with Ward A coverage in restructured hospitals and access to specialist outpatient services.', '30 days', 'Annual renewable', 'Ward A coverage'),
    'AIA MediShield Gold Max':   ('Premium hospitalisation plan with private hospital coverage and no sub-limits on hospitalisation benefits, integrated with MediShield Life.', '30 days', 'Annual renewable', 'Private hospital, no sub-limits'),
    'AIA MediShield Platinum':   ('Ultra-premium hospitalisation plan with unlimited private hospital coverage, overseas emergency benefits, and medical evacuation.', '30 days', 'Annual renewable', 'Worldwide coverage including medical evacuation'),
    'AIA HealthPlus Essential':  ('Outpatient-focused health plan providing strong specialist consultation and diagnostic investigation benefits.', '30 days', 'Annual renewable', 'Enhanced outpatient and specialist benefits'),
    'AIA HealthPlus Comprehensive':('Balanced health plan covering both inpatient hospitalisation and outpatient specialist treatment with competitive sub-limits.', '30 days', 'Annual renewable', 'Balanced inpatient and outpatient coverage'),
    'AIA HealthPlus Premier':    ('Executive-grade health plan with access to executive ward and unlimited specialist consultations.', '30 days', 'Annual renewable', 'Executive ward and unlimited specialist access'),
    'AIA CareShield Basic':      ('Simplified health plan for young adults with fast digital approval and essential hospitalisation coverage.', '30 days', 'Annual renewable', 'Digital-first, simplified underwriting'),
    'AIA CareShield Family':     ('Family health plan extending coverage to spouse and children, with newborn rider for immediate coverage of newborns.', '30 days', 'Annual renewable', 'Family coverage with newborn rider'),
    'AIA CancerCare Protect':    ('Specialised health plan focusing on cancer treatment costs including chemotherapy, radiotherapy, and targeted therapy.', '30 days', 'Annual renewable', 'Cancer treatment and recovery focus'),
    'AIA MaternaCare':           ('Women\'s health plan covering maternity hospitalisation, complications of pregnancy, and newborn care benefits.', '10 months', 'Annual renewable', 'Maternity and newborn coverage'),
    'AIA SeniorCare Shield':     ('Health plan for policyholders aged 55 and above, with no age exit and senior-specific hospitalisation benefits.', '30 days', 'Annual renewable', 'No age exit, senior-focused benefits'),
    'AIA GlobalCare Elite':      ('International health plan for expatriates and frequent travellers, with worldwide coverage and medical evacuation services.', '30 days', 'Annual renewable', 'Worldwide coverage and medical evacuation'),
    'AIA WellnessPlus Rider':    ('Supplementary wellness rider providing benefits for dental treatment, optical, and health screening expenses.', 'None', 'Annual renewable', 'Dental, vision, and wellness supplement'),
    # CRITICAL ILLNESS
    'AIA CI Essential 5':        ('Essential critical illness plan covering the five most common life-threatening conditions as defined under the LIA CI Framework.', '90 days', 'Lump sum on diagnosis', '5 core conditions'),
    'AIA CI Protect 10':         ('Critical illness plan covering ten serious conditions with enhanced clinical definitions aligned with the LIA CI Framework.', '90 days', 'Lump sum on diagnosis', '10 conditions covered'),
    'AIA CI Protect 36':         ('Comprehensive critical illness plan covering thirty-six conditions across early, intermediate, and advanced stages.', '90 days', 'Lump sum on diagnosis', '36 conditions covered'),
    'AIA CI Protect 53':         ('Premium critical illness plan with the broadest coverage of fifty-three conditions, including rare and serious diseases.', '90 days', 'Lump sum on diagnosis', '53 conditions, broadest coverage'),
    'AIA CI MultiClaim':         ('Advanced critical illness plan allowing multiple claims for the same or different critical illnesses throughout the policy term.', '90 days', 'Multiple lump sum claims', 'Multiple claims permitted'),
    'AIA EarlyCI Basic':         ('Early-stage critical illness plan paying a benefit on diagnosis at early and intermediate stages, before the condition becomes advanced.', '90 days', 'Early and intermediate stage payout', 'Early stage coverage'),
    'AIA EarlyCI Premier':       ('Premium early-stage CI plan with enhanced early stage benefits and a recurrence benefit for subsequent CI diagnoses.', '90 days', 'Early stage plus recurrence benefit', 'Recurrence benefit included'),
    'AIA CancerGuard Plus':      ('Cancer-specific critical illness plan offering a high sum assured exclusively for cancer diagnosis at any stage.', '90 days', 'Lump sum on cancer diagnosis', 'Cancer-only, high coverage'),
    'AIA HeartGuard Plus':       ('Cardiac-focused critical illness plan covering heart attack, stroke, and cardiovascular conditions with clinical precision.', '90 days', 'Lump sum on diagnosis', 'Cardiac and cardiovascular focus'),
    'AIA CI Monthly Income':     ('Critical illness plan structured to pay a monthly income benefit upon CI diagnosis, rather than a lump sum, to replace lost income.', '90 days', 'Monthly income on diagnosis', 'Monthly income structure'),
    'AIA CI Protect 360':        ('All-stage critical illness plan covering early, intermediate, and advanced stages of thirty-six conditions, with separate benefit amounts per stage.', '90 days', 'Multi-stage payouts', 'All-stage coverage'),
    'AIA SeniorCI Cover':        ('Senior-specific critical illness plan for policyholders aged 50 to 70, with simplified underwriting and five core conditions covered.', '90 days', 'Lump sum on diagnosis', 'Senior-focused, simplified underwriting'),
    'AIA CI FamilyCare':         ('Family critical illness plan with optional child CI rider providing coverage for children\'s critical illnesses from birth.', '90 days', 'Lump sum on diagnosis', 'Family plan with child rider'),
    'AIA CI BusinessGuard':      ('Business critical illness plan providing a lump sum to the business upon the CI diagnosis of a key person or business owner.', '90 days', 'Lump sum to business', 'Business continuity coverage'),
    'AIA DreadDisease Premier':  ('Ultra-comprehensive dread disease plan covering over sixty serious medical conditions for high-net-worth individuals requiring maximum protection.', '90 days', 'Lump sum on diagnosis', '60+ conditions, maximum coverage'),
    # DISABILITY
    'AIA DisabilityGuard Basic': ('Disability income plan providing monthly benefit under own occupation definition for the first two years, thereafter any occupation.', '90 days', 'Own occupation 2 years, any thereafter', 'Entry-level disability income'),
    'AIA DisabilityGuard Plus':  ('Disability income plan with own occupation definition maintained for five years, offering professional-grade income protection.', '90 days', 'Own occupation 5 years', 'Extended own occupation period'),
    'AIA DisabilityGuard Premier':('Premium disability income plan maintaining own occupation definition to age 65, for high-income professionals requiring maximum protection.', '90 days', 'Own occupation to age 65', 'Own occupation for entire benefit period'),
    'AIA IncomeShield Basic':    ('Affordable disability income plan using any occupation definition, providing basic income replacement at a lower premium.', '90 days', 'Any occupation definition', 'Budget-friendly income protection'),
    'AIA IncomeShield Plus':     ('Enhanced disability income plan with any occupation definition and additional rehabilitation benefit for return-to-work support.', '90 days', 'Any occupation with rehab benefit', 'Enhanced rehabilitation support'),
    'AIA IncomeShield Premier':  ('Comprehensive disability income plan combining own and any occupation definitions with TPD lump sum and rehabilitation benefit.', '90 days', 'Comprehensive income protection', 'All-round disability coverage'),
    'AIA TotalCover Disability': ('Disability plan combining monthly income benefit during total disability with a lump sum TPD benefit upon permanent disability.', '90 days', 'Monthly income plus TPD lump sum', 'Dual benefit structure'),
    'AIA OccupationProtect':     ('Disability income plan with occupation-specific definitions tailored for trade, technical, and manual workers.', '90 days', 'Occupation-specific definitions', 'Trade and manual worker focus'),
    'AIA ExecutiveDisability':   ('High-income executive disability plan with own occupation definition for the full benefit period and high monthly benefit limits.', '90 days', 'Own occupation, high income replacement', 'C-suite and executive coverage'),
    'AIA FreelanceShield':       ('Disability income plan designed for self-employed individuals with flexible income proof requirements and own occupation definition.', '90 days', 'Flexible income proof', 'Self-employed friendly'),
    'AIA AccidentDisability':    ('Accident-only disability income plan providing monthly benefit solely for disabilities arising from accidental causes, at a very low premium.', '90 days', 'Accidental disability only', 'Lowest premium, accident-only'),
    'AIA RehabPlus Disability':  ('Disability income plan with an enhanced rehabilitation benefit equal to 75% of the monthly benefit during approved rehabilitation programmes.', '90 days', 'Enhanced rehabilitation benefit 75%', 'Recovery and return-to-work focus'),
    'AIA PartialDisability Cover':('Disability plan with a strong partial permanent disability benefit, providing proportionate payouts based on the degree of disability.', '90 days', 'Strong PPD benefit schedule', 'Partial disability focus'),
    'AIA SeniorDisability Shield':('Disability income plan for policyholders aged 50 to 65 with simplified underwriting and any occupation definition.', '90 days', 'Senior-specific, simplified underwriting', 'Ages 50 to 65'),
    'AIA GroupDisability SME':   ('Group disability income plan for small and medium enterprises, providing employees with income protection at group premium rates.', '90 days', 'Group rates for SMEs', 'Group coverage for businesses'),
}

# ── DEFINITIONS BY POLICY TYPE ────────────────────────────────────────────────
DEFINITIONS = {
'life': [
 ('"Policy"','This Policy Contract, together with the Policy Schedule, any endorsements, riders, and addenda attached hereto, constitutes the entire contract of insurance between the Company and the Policy Owner. In the event of any inconsistency between the Policy Schedule and the general terms and conditions, the Policy Schedule shall prevail.'),
 ('"Company" / "We" / "Us" / "Our"','AIA Singapore Pte. Ltd. (Reg. No. 202600001Z), a company duly incorporated in Singapore and licensed by the Monetary Authority of Singapore ("MAS") to carry on life insurance business pursuant to the Insurance Act 1966 (Cap. 142).'),
 ('"Policy Owner" / "You" / "Your"','The person named as Policy Owner in the Policy Schedule, being the party who has entered into this contract of insurance with the Company and who is responsible for the payment of Premiums. The Policy Owner may or may not be the same person as the Insured.'),
 ('"Insured" / "Life Assured"','The person named as the Insured in the Policy Schedule, on whose life this Policy is issued and upon whose death, disability, or other insured event the benefits under this Policy become payable.'),
 ('"Sum Assured"','The principal benefit amount stated in the Policy Schedule, representing the maximum lump sum payable upon the occurrence of the insured event, subject to the terms, conditions, and exclusions of this Policy.'),
 ('"Premium"','The amount payable by the Policy Owner to the Company as consideration for the insurance coverage provided under this Policy, in the frequency and amount stated in the Policy Schedule.'),
 ('"Death"','The permanent and irreversible cessation of all biological functions that sustain a living organism, confirmed by a registered medical practitioner and evidenced by an official death certificate issued by the Registry of Births and Deaths, Singapore, or an equivalent authority.'),
 ('"Accidental Death"','Death caused solely, directly, and independently of all other causes by violent, external, and visible means resulting from an accident, provided such death occurs within three hundred and sixty-five (365) calendar days of the accident. Accidental Death expressly excludes death caused or contributed to by disease, illness, bodily infirmity, surgical treatment, self-inflicted injury, or the ingestion of drugs or alcohol not prescribed by a registered medical practitioner.'),
 ('"Total and Permanent Disability" ("TPD")','A physical or mental condition caused by Injury or Sickness which wholly and continuously prevents the Insured from engaging in any occupation, business, or activity for income, remuneration, or profit; which has persisted for a continuous and uninterrupted period of not less than six (6) consecutive months; and which, in the opinion of a specialist registered with the Singapore Medical Council ("SMC"), is permanent and irrecoverable with no reasonable prospect of improvement.'),
 ('"Beneficiary" / "Nominee"','The person or persons designated to receive the policy proceeds upon the death of the Insured, as named in the Policy Schedule or as subsequently nominated by the Policy Owner in writing to the Company, subject to the provisions of Section 49L of the Insurance Act 1966 and any valid assignment of this Policy.'),
 ('"Grace Period"','A period of thirty (30) calendar days from each Premium Due Date during which this Policy shall remain in force notwithstanding non-payment of the Premium, without prejudice to the Company\'s right to deduct any outstanding Premium from any benefit payable.'),
 ('"Incontestability Period"','A period of two (2) years commencing from the Issue Date or the date of reinstatement of this Policy, after which the Company shall not contest the validity of this Policy on grounds of misrepresentation or non-disclosure, except in cases of fraud.'),
 ('"Suicide Exclusion Period"','A period of one (1) year commencing from the Issue Date or date of reinstatement of this Policy during which the Company\'s liability is limited to a refund of Premiums paid (without interest) if the Insured, whether sane or insane, dies by suicide.'),
 ('"Policy Term"','The period of coverage under this Policy commencing on the Issue Date and ending on the Expiry Date as stated in the Policy Schedule, subject to earlier termination in accordance with the terms herein.'),
 ('"Issue Date" / "Commencement Date"','The date on which this Policy commences and coverage begins, as stated in the Policy Schedule, being the date upon which the Company\'s liability under this Policy first arises.'),
],
'health': [
 ('"Policy"','This Policy Contract, together with the Policy Schedule, Schedule of Benefits, endorsements, and any addenda attached hereto, constitutes the entire contract of insurance. The Schedule of Benefits shall prevail in the event of any conflict with the general terms and conditions.'),
 ('"Company" / "We" / "Us" / "Our"','AIA Singapore Pte. Ltd. (Reg. No. 202600001Z), duly licensed by the Monetary Authority of Singapore to carry on accident and health insurance business pursuant to the Insurance Act 1966 (Cap. 142).'),
 ('"Insured"','The individual named as the Insured in the Policy Schedule whose medical expenses and hospitalisation costs are covered under this Policy.'),
 ('"Hospitalisation"','The admission of the Insured as an inpatient to an Approved Hospital upon the written advice of a registered medical practitioner, for a period of not less than six (6) consecutive hours, for the purpose of medical treatment that cannot be adequately or appropriately provided on an outpatient or day surgery basis.'),
 ('"Approved Hospital"','A hospital, specialist centre, or medical institution in Singapore that: (i) is duly licensed by the Ministry of Health Singapore ("MOH"); (ii) is operated primarily for the care and treatment of sick and injured persons; (iii) provides twenty-four (24) hour nursing service; and (iv) is recognised by the Company. The Company maintains a current list of Approved Hospitals at www.aia-s.com.sg.'),
 ('"Medically Necessary"','A medical service, treatment, procedure, or supply that: (i) is required for the diagnosis or treatment of a Sickness or Injury; (ii) is consistent with generally accepted standards of medical practice in Singapore; (iii) is not primarily for the convenience of the Insured or the attending physician; and (iv) is not of an experimental or investigational nature.'),
 ('"Pre-existing Condition"','Any Sickness, disease, injury, or medical condition which the Insured had prior to the Issue Date, and for which the Insured received or was advised to receive medical treatment, diagnosis, consultation, or prescribed medication within the twelve (12) months immediately preceding the Issue Date.'),
 ('"Sickness"','Any disease, illness, or bodily disorder contracted and commencing after the Issue Date of this Policy (or after any applicable waiting period), which requires treatment by a registered medical practitioner.'),
 ('"Injury"','Bodily harm caused solely and directly by violent, external, and visible means, occurring after the Issue Date of this Policy, independently of any disease, infirmity, or Pre-existing Condition.'),
 ('"Surgical Procedure"','A procedure performed by a registered surgeon in an Approved Hospital operating theatre, requiring the administration of anaesthesia and involving an incision into body tissues for diagnostic or therapeutic purposes, as classified under the Ministry of Health Singapore Table of Surgical Procedures ("MOH Table").'),
 ('"Eligible Expenses"','Reasonable and customary charges for Medically Necessary treatment which do not exceed the usual charges for similar treatment in Singapore, as determined by the Company acting reasonably and in good faith.'),
 ('"MediShield Life"','The national health insurance scheme administered by the Central Provident Fund Board pursuant to the MediShield Life Scheme Act 2015.'),
 ('"Deductible"','The fixed amount of Eligible Expenses which the Insured is required to bear in each Policy Year before the Company\'s reimbursement obligation commences, as stated in the Schedule of Benefits.'),
 ('"Co-insurance"','The percentage of Eligible Expenses (after deduction of the Deductible and any MediShield Life payout) which the Insured is required to bear, as stated in the Schedule of Benefits.'),
 ('"Policy Year"','A period of twelve (12) consecutive months commencing on the Issue Date or any Policy Anniversary thereafter.'),
],
'critical_illness': [
 ('"Policy"','This Policy Contract, together with the Policy Schedule, any endorsements, and addenda, constitutes the entire agreement between the Company and the Policy Owner with respect to critical illness coverage. The definitions of Critical Illnesses set out herein are aligned with the Life Insurance Association Singapore ("LIA") Critical Illness (CI) Framework.'),
 ('"Company" / "We" / "Us" / "Our"','AIA Singapore Pte. Ltd. (Reg. No. 202600001Z), licensed by the Monetary Authority of Singapore to carry on life and accident and health insurance business in Singapore.'),
 ('"Critical Illness"','Any one of the serious medical conditions defined under Section 3 of this Policy, as precisely defined herein in accordance with the LIA CI Framework applicable as at the Issue Date.'),
 ('"Diagnosis"','The definitive and unequivocal determination of a Critical Illness by a Specialist, based on clinical findings, laboratory investigations, histopathological examination, imaging studies, or such other objective medical evidence as is appropriate to the condition.'),
 ('"Specialist"','A medical practitioner holding valid specialist registration with the Singapore Medical Council ("SMC") in the relevant field of medicine pertaining to the Critical Illness being diagnosed, who is not the Insured, the Policy Owner, or a family member of either.'),
 ('"Survival Period"','A continuous period of thirty (30) calendar days immediately following the date of Diagnosis of a Critical Illness during which the Insured must remain alive for the Critical Illness Benefit to become payable.'),
 ('"Cancer"','A malignant tumour characterised by the uncontrolled growth and spread of malignant cells with invasion and destruction of normal tissue, confirmed by histological examination. The following are excluded: carcinoma-in-situ; pre-malignant tumours; all skin cancers other than invasive malignant melanoma at Clark Level IV or V; papillary thyroid microcarcinoma less than 1cm; prostate cancer T1a or T1b; and chronic lymphocytic leukaemia less than RAI Stage 3.'),
 ('"Heart Attack"','Death of a portion of the myocardium confirmed by: (i) clinical history of typical ischaemic chest pain; (ii) new ECG changes consistent with acute MI; and (iii) elevation of cardiac biomarkers at diagnostic levels. Unstable angina or troponin elevation without diagnostic ECG changes are excluded.'),
 ('"Stroke"','A cerebrovascular incident producing neurological sequelae lasting more than twenty-four (24) hours and resulting in permanent neurological deficit confirmed by a neurologist at least three (3) months after the acute event. TIAs and reversible neurological deficits are excluded.'),
 ('"Kidney Failure"','End-stage renal disease requiring maintenance dialysis or renal transplantation. Acute or reversible renal failure is excluded.'),
 ('"Major Organ Transplant"','Transplantation of heart, heart-lung complex, liver, kidney, pancreas, or bone marrow as recipient, necessitated by irreversible organ failure. Transplantation of cornea, skin, cartilage, or other tissues is excluded.'),
 ('"LIA CI Framework"','The standardised definitions for critical illnesses established by the Life Insurance Association Singapore, adopted by this Policy as at the Issue Date.'),
 ('"Waiting Period"','A period of ninety (90) calendar days from the Issue Date during which no Critical Illness Benefit is payable, applicable to all covered conditions without exception.'),
 ('"Sum Assured"','The lump sum benefit payable upon confirmation of a qualifying Diagnosis and satisfaction of the Survival Period, as stated in the Policy Schedule.'),
],
'disability': [
 ('"Policy"','This Policy Contract, together with the Policy Schedule, Schedule of Benefits, any endorsements, and addenda, constitutes the entire disability income insurance contract between the parties.'),
 ('"Company" / "We" / "Us" / "Our"','AIA Singapore Pte. Ltd. (Reg. No. 202600001Z), licensed by the Monetary Authority of Singapore to carry on accident and health insurance business in Singapore.'),
 ('"Total Disability"','A physical or mental condition caused by Injury or Sickness which wholly and continuously prevents the Insured from: (i) during the first twenty-four (24) months — performing each and every material duty of the Insured\'s Own Occupation; and (ii) thereafter — engaging in any occupation, business, or activity for income, remuneration, or profit for which the Insured is reasonably qualified by education, training, or experience.'),
 ('"Partial Disability"','A physical or mental condition caused by Injury or Sickness which prevents the Insured from performing one or more material duties of the Insured\'s Own Occupation, or causes the Insured to work in a reduced capacity resulting in a loss of Pre-disability Earned Income of at least twenty percent (20%).'),
 ('"Total Permanent Disability" ("TPD")','A Total Disability which, in the certified opinion of a Specialist, is permanent, irreversible, and irrecoverable, with no reasonable prospect of improvement, and which has continued without interruption for not less than six (6) consecutive months.'),
 ('"Own Occupation"','The occupation in which the Insured was regularly and gainfully engaged on a full-time basis at the time of disability onset, as declared in the application and as stated in the Policy Schedule.'),
 ('"Elimination Period"','The qualifying waiting period of ninety (90) consecutive days of continuous Total Disability, commencing from the first day of disability, which must be fully satisfied before any Monthly Benefit becomes payable.'),
 ('"Monthly Benefit"','The monthly income benefit amount payable to the Insured during a qualifying period of Total Disability, as stated in the Policy Schedule, subject to the offsets, limitations, and conditions of this Policy.'),
 ('"Benefit Period"','The maximum aggregate period during which the Monthly Benefit is payable in respect of any single continuous period of Total Disability, as specified in the Policy Schedule.'),
 ('"Pre-disability Earned Income"','The Insured\'s average monthly gross income from employment or self-employment, calculated over the twelve (12) months immediately preceding the onset of disability, as evidenced by IRAS assessments, payslips, or other documentary evidence.'),
 ('"Specialist"','A medical practitioner holding valid specialist registration with the SMC in the relevant field, who is not the Insured, the Policy Owner, or a family member of either.'),
 ('"Recurrent Disability"','A subsequent period of Total Disability arising from the same or related cause as a prior disability, commencing within six (6) months of recovery. Treated as a continuation; Elimination Period does not apply anew.'),
 ('"Rehabilitation Benefit"','An additional benefit payable where the Insured is participating in a formal occupational rehabilitation programme approved by the Company, aimed at enabling return to gainful employment.'),
 ('"Waiver of Premium"','A provision whereby the Company waives all Premiums falling due during a qualifying period of Total Disability, after the Elimination Period is satisfied.'),
],
}

BENEFITS = {
'life': [
("3.1","Death Benefit","Subject to the terms and conditions of this Policy, upon receipt of due proof satisfactory to the Company that the Insured has died while this Policy is in force, the Company shall pay the Sum Assured as stated in the Policy Schedule to the Beneficiary or the legal personal representative of the Insured's estate. Payment shall constitute full and final discharge of the Company's obligations under this Policy, and the Policy shall thereupon terminate."),
("3.2","Accidental Death Benefit","Where the Insured's death is caused solely, directly, and independently of all other causes by an Accidental Death, occurring within three hundred and sixty-five (365) calendar days of the accident, the Company shall pay an additional benefit equal to one hundred percent (100%) of the Sum Assured in addition to the Death Benefit payable under Clause 3.1. The total aggregate benefit under Clauses 3.1 and 3.2 shall not exceed two hundred percent (200%) of the Sum Assured. This benefit requires a police or coroner's report confirming the accidental cause of death."),
("3.3","Total and Permanent Disability (TPD) Benefit","Upon receipt of satisfactory proof that the Insured has suffered Total and Permanent Disability while this Policy is in force, and the Insured has not attained the age of seventy (70) years at the commencement of the disability, the Company shall pay the TPD Benefit equal to the Sum Assured as a lump sum. Upon payment, this Policy shall terminate. The Death Benefit and TPD Benefit shall not both be payable in respect of the same Insured."),
("3.4","Waiting Period Provision","No benefit (other than the Accidental Death Benefit where death is caused solely by an accident) shall be payable in respect of any event arising within ninety (90) calendar days of the Issue Date. This waiting period applies upon reinstatement, commencing from the date of reinstatement."),
("3.5","Simultaneous Events","Where more than one benefit would otherwise be payable in respect of the same event, the Company shall pay only the highest applicable benefit. The Death Benefit and TPD Benefit shall not be concurrently payable."),
("3.6","Currency of Payment","All benefits are paid in Singapore Dollars (SGD). Where the insured event occurs outside Singapore, any foreign currency amounts shall be converted to SGD at the Company's prevailing exchange rate at the date of the event."),
],
'health': [
("3.1","Hospitalisation Benefit","Subject to the terms and conditions of this Policy and the Schedule of Benefits, the Company shall reimburse Eligible Expenses incurred for Hospitalisation in an Approved Hospital, up to the annual limit stated in the Schedule of Benefits per Policy Year. Hospitalisation must be certified as Medically Necessary by the attending physician, and the minimum duration of continuous inpatient stay shall be six (6) consecutive hours, save in cases of emergency admission or day surgery."),
("3.2","Surgical Benefit","The Company shall reimburse Eligible Expenses incurred for Surgical Procedures performed in an Approved Hospital, classified under the MOH Table current at the date of surgery. The reimbursement shall not exceed the limits in the Schedule of Benefits. Cosmetic, aesthetic, or elective procedures that are not Medically Necessary are expressly excluded."),
("3.3","Outpatient Specialist Benefit","The Company shall reimburse Eligible Expenses for Outpatient Treatment received from a registered specialist at an Approved Hospital or recognised specialist clinic, up to the sub-limit in the Schedule of Benefits per Policy Year. General practitioner consultations, health screenings, and preventive care are not covered."),
("3.4","Emergency Treatment Benefit","The Company shall reimburse Eligible Expenses for emergency treatment at the A&E department of an Approved Hospital, necessitated by a sudden and acute Injury or life-threatening Sickness. Emergency treatment outside Singapore is subject to a sub-limit as stated in the Schedule of Benefits."),
("3.5","MediShield Life Co-ordination","Where the Insured is covered under MediShield Life, claims shall be co-ordinated such that total benefits from all sources shall not exceed the Eligible Expenses actually incurred. The Company shall reimburse the excess Eligible Expenses not covered by MediShield Life, after application of the applicable Deductible and Co-insurance."),
("3.6","Pre-existing Condition Waiting Period","No benefit is payable in respect of any Pre-existing Condition unless declared and accepted by the Company in writing. Benefits for Sickness are subject to a thirty (30) calendar day waiting period from the Issue Date. No waiting period applies to treatment arising from an Injury."),
("3.7","Benefit Limits and Cost-Sharing","All benefits are subject to: (i) the annual and lifetime limits in the Schedule of Benefits; (ii) the Deductible which must be satisfied each Policy Year before reimbursement begins; and (iii) the Co-insurance rate representing the Insured's share of Eligible Expenses after the Deductible."),
],
'critical_illness': [
("3.1","Critical Illness Benefit — General","Upon receipt of satisfactory proof that the Insured has been diagnosed with any one (1) of the Critical Illnesses defined herein, while this Policy is in force, and provided the Insured survives the Survival Period of thirty (30) calendar days following Diagnosis, the Company shall pay the Sum Assured as a lump sum. Payment shall constitute full and final discharge of the Company's obligations and this Policy shall terminate."),
("3.2","Cancer","The Company shall pay the Critical Illness Benefit upon confirmed Diagnosis of Cancer, confirmed by histological or cytological examination by a registered pathologist. The following are excluded: carcinoma-in-situ; pre-malignant tumours; all primary skin cancers other than invasive malignant melanoma at Clark Level IV or above; papillary thyroid microcarcinoma less than one (1) centimetre without nodal or distant metastasis; prostate cancers classified as T1a or T1b; and chronic lymphocytic leukaemia at RAI Stage 1 or 2."),
("3.3","Heart Attack","The Company shall pay the Critical Illness Benefit upon Diagnosis of Heart Attack, confirmed by all three of the following: (i) clinical presentation of acute ischaemic chest pain; (ii) new ECG changes including new ST elevation, pathological Q-waves, or new LBBB; and (iii) cardiac biomarker elevation at diagnostic levels (Troponin I above 1.0 ng/mL or Troponin T above 0.1 ng/mL). Unstable angina and demand ischaemia are excluded."),
("3.4","Stroke","The Company shall pay the Critical Illness Benefit upon Diagnosis of Stroke, being a cerebrovascular incident producing neurological deficit persisting more than twenty-four (24) hours and confirmed as permanent by a neurologist at least three (3) months after the acute event, supported by neuroimaging findings. TIAs, reversible neurological deficits, and lacunar infarcts without permanent deficit are excluded."),
("3.5","Kidney Failure","The Company shall pay the Critical Illness Benefit upon Diagnosis of Kidney Failure, being end-stage bilateral renal failure requiring maintenance dialysis for not less than two (2) months, or bilateral renal transplantation. Acute or reversible renal failure is excluded."),
("3.6","Major Organ Transplant","The Company shall pay the Critical Illness Benefit where the Insured has undergone transplantation of heart, heart-lung complex, liver, kidney, pancreas, or bone marrow as recipient, necessitated by irreversible organ failure, in an Approved Hospital. Transplantation of cornea, skin, cartilage, or autologous tissue is excluded."),
("3.7","Survival Period Condition","No Critical Illness Benefit is payable if the Insured dies within thirty (30) calendar days of Diagnosis. In such circumstances, only any applicable death benefit under a separate life insurance policy shall be considered."),
],
'disability': [
("3.1","Total Disability Benefit — Monthly Income","Subject to satisfaction of the Elimination Period and the terms of this Policy, where the Insured suffers Total Disability while this Policy is in force, the Company shall pay the Monthly Benefit for each complete calendar month of continuous Total Disability, commencing from expiry of the Elimination Period, for the duration of the Benefit Period or until earlier cessation of Total Disability, death, or the Expiry Date."),
("3.2","Partial Disability Benefit","Where the Insured suffers Partial Disability following qualifying Total Disability, the Company shall pay: (Pre-disability Earned Income minus Current Earned Income) divided by Pre-disability Earned Income, multiplied by the Monthly Benefit. Payable for up to six (6) months per disability period. Not concurrently payable with Total Disability Monthly Benefit."),
("3.3","Total Permanent Disability (TPD) Lump Sum","Where the Insured suffers Total Permanent Disability while this Policy is in force and before attaining age sixty-five (65), the Company shall pay, in addition to Monthly Benefit already paid, a lump sum TPD Benefit equal to twelve (12) times the Monthly Benefit. This does not affect continued Monthly Benefit payment for the remainder of the Benefit Period."),
("3.4","Elimination Period","No Monthly Benefit or Partial Disability Benefit is payable in respect of any period of disability falling within the ninety (90) consecutive day Elimination Period. The Elimination Period must be satisfied afresh for each new unrelated period of disability."),
("3.5","Rehabilitation Benefit","Where the Insured participates in a Company-approved formal occupational rehabilitation programme while receiving the Monthly Benefit, the Company shall pay an additional Rehabilitation Benefit equal to fifty percent (50%) of the Monthly Benefit for the duration of the approved programme, up to twelve (12) months."),
("3.6","Waiver of Premium","During any continuous period of Total Disability for which the Monthly Benefit is being paid (after satisfying the Elimination Period), the Company shall waive all Premiums falling due until the earlier of: recovery; the Insured attaining age sixty-five (65); or the Expiry Date."),
("3.7","Recurrent Disability","If the Insured returns to work and is subsequently disabled by the same or related cause within six (6) months of recovery, the subsequent disability is treated as a continuation of the prior period and the Elimination Period does not apply anew. Disability commencing more than six (6) months after recovery is treated as a new and separate disability."),
],
}

EXCLUSIONS = {
'life': [
"Death or Total Permanent Disability arising directly or indirectly from a Pre-existing Condition not fully disclosed in the application, whether or not the Policy Owner was aware of such condition.",
"Death or TPD caused by: (i) self-inflicted injury; (ii) suicide within the Suicide Exclusion Period of one (1) year from Issue Date or reinstatement; provided that after the Suicide Exclusion Period, death by suicide is covered.",
"Death or TPD arising from participation in criminal acts, illegal activities, civil unrest, riot, or unlawful assembly.",
"Death or TPD caused by war, invasion, act of foreign enemy, hostilities, civil war, rebellion, revolution, or insurrection, whether declared or undeclared.",
"Death or TPD arising from voluntary consumption of alcohol above the legal driving limit, non-prescribed drugs, or solvent abuse.",
"Death or TPD caused by nuclear reaction, radiation, or radioactive contamination.",
"Death or TPD arising from aviation activity other than as a fare-paying passenger on a scheduled commercial airline on a licensed route.",
"Fraudulent misrepresentation, non-disclosure, or fraud in connection with this Policy or any claim.",
],
'health': [
"Treatment for Pre-existing Conditions not declared and accepted by the Company in writing.",
"Cosmetic, aesthetic, or beauty treatments or procedures that are not Medically Necessary.",
"Pregnancy, childbirth, miscarriage, abortion, or complications thereof, except where covered under an approved maternity rider.",
"Psychiatric, psychological, or mental health disorders, except as expressly covered under a specific mental health rider.",
"Treatment arising from use or misuse of alcohol, narcotics, drugs, or psychotropic substances not prescribed by a registered medical practitioner.",
"Experimental, unproven, or investigational treatments, procedures, or drugs not approved by the Ministry of Health Singapore or HSA.",
"Treatment received outside an Approved Hospital, except for emergency treatment as provided under Clause 3.4.",
"Injuries arising from war, civil unrest, riot, criminal acts, or aviation other than as a fare-paying passenger on a scheduled commercial airline.",
"Dental treatment unless necessitated directly by accidental Injury to sound and natural teeth.",
"Routine health screenings, check-ups, vaccinations, immunisations, and preventive healthcare.",
"Congenital conditions, congenital abnormalities, or hereditary conditions.",
"Refractive eye conditions and corrective procedures unless arising from accidental Injury.",
],
'critical_illness': [
"Any Critical Illness diagnosed within the Waiting Period of ninety (90) calendar days from the Issue Date or any date of reinstatement.",
"Any Critical Illness caused by a Pre-existing Condition not declared and accepted in writing.",
"Any condition not meeting the precise clinical criteria in Section 2 (Definitions) and Section 3 (Benefit Provisions), regardless of medical label applied.",
"HIV infection, AIDS, and all related conditions, however contracted.",
"Any Critical Illness caused by self-inflicted injury, attempted suicide, substance abuse, or alcohol consumption above the legal limit.",
"Any Critical Illness caused by war, invasion, act of foreign enemy, civil war, rebellion, or terrorism.",
"Any Critical Illness arising from hazardous activities not declared in the application and accepted in writing.",
"Failure to satisfy the Survival Period of thirty (30) calendar days following Diagnosis.",
"Any Diagnosis made outside Singapore by a physician not holding specialist registration with the SMC or equivalent, without prior written consent.",
"Any condition arising from nuclear fission, nuclear fusion, or radioactive contamination.",
],
'disability': [
"Disability arising from a Pre-existing Condition not declared and accepted by the Company in writing.",
"Disability caused by intentional self-inflicted injury, attempted suicide, or participation in criminal acts.",
"Disability arising from normal pregnancy or childbirth, or complications of pregnancy.",
"Disability caused by war, invasion, act of foreign enemy, hostilities, civil war, military operations, or terrorism.",
"Disability from voluntary use or abuse of alcohol, narcotics, or non-prescribed psychoactive substances.",
"Disability from aviation other than as a fare-paying passenger on a scheduled commercial airline, or from undeclared hazardous activities.",
"Disability attributable solely to psychiatric or psychological conditions, unless the Company has expressly agreed to cover such conditions by endorsement.",
"Disability for which no objective medical evidence of functional impairment can be established.",
"Disability arising during full-time military, naval, or air force service.",
"Disability caused by nuclear fission, nuclear fusion, or radioactive contamination.",
"Disability commencing after the Expiry Date or after the Insured attains age sixty-five (65).",
],
}

GENERAL_PROVISIONS = {
'life': [
("7.1","Entire Contract","This Policy, the Policy Schedule, the application form, and all endorsements constitute the entire contract. No agent has authority to modify any provision unless in a written endorsement signed by a duly authorised officer."),
("7.2","Incontestability","After this Policy has been in force for two (2) years from Issue Date or reinstatement, the Company shall not contest its validity except on grounds of fraud."),
("7.3","Suicide","If the Insured dies by suicide within one (1) year of Issue Date or reinstatement, the Company's liability is limited to a refund of Premiums paid (without interest). Thereafter, death by suicide is covered."),
("7.4","Misrepresentation","Material misrepresentation or non-disclosure entitles the Company to: (i) void this Policy from inception; (ii) deny claims; or (iii) impose additional terms."),
("7.5","Free Look Period","The Policy Owner has twenty-one (21) days from receipt to cancel this Policy for a full refund of Premiums paid, less any medical expenses incurred."),
("7.6","Governing Law","This Policy is governed by the laws of Singapore. Disputes are subject to the non-exclusive jurisdiction of Singapore courts."),
("7.7","Policy Owners' Protection Scheme","This Policy is protected under the PPF Scheme administered by SDIC. Visit www.sdic.org.sg for details."),
("7.8","Personal Data Protection","Personal data is collected and processed in accordance with the PDPA 2012 for policy administration, underwriting, claims, regulatory compliance, and fraud detection."),
],
'health': [
("7.1","Entire Contract","This Policy, the Policy Schedule, Schedule of Benefits, application form, and endorsements constitute the entire contract of health insurance."),
("7.2","Renewal","This Policy is renewable annually subject to the Company's prevailing terms, payment of renewal Premium, and the Company's right to decline renewal or impose special terms based on claims experience."),
("7.3","Premium Adjustment","The Company may revise the Premium at each renewal based on attained age, claims experience, and medical inflation, with thirty (30) days' written notice."),
("7.4","Misrepresentation","Material misrepresentation or non-disclosure entitles the Company to void this Policy and deny all claims."),
("7.5","Free Look Period","Twenty-one (21) days from receipt to cancel for a full refund of Premiums paid, less any claims paid or medical expenses incurred."),
("7.6","Subrogation","Upon payment of any benefit, the Company is subrogated to the Insured's rights against any third party responsible for the Sickness or Injury."),
("7.7","Governing Law","Governed by the laws of Singapore. Disputes subject to Singapore court jurisdiction."),
("7.8","Policy Owners' Protection Scheme","Protected under the PPF Scheme administered by SDIC."),
],
'critical_illness': [
("7.1","Entire Contract","This Policy, the Policy Schedule, application form, and endorsements constitute the entire critical illness insurance contract."),
("7.2","Incontestability","After two (2) years from Issue Date or reinstatement, the Company shall not contest validity except on grounds of fraud."),
("7.3","Non-duplication","If the Insured is covered under more than one CI policy issued by the Company, the Company's total liability shall not exceed the Sum Assured under this Policy."),
("7.4","Misrepresentation","Material misrepresentation or non-disclosure entitles the Company to void this Policy and deny all claims."),
("7.5","Free Look Period","Twenty-one (21) days from receipt to cancel for a full refund of Premiums paid."),
("7.6","LIA CI Framework Compliance","CI definitions are aligned with the LIA CI Framework. Amendments to the Framework may be adopted by the Company with MAS approval and prior notice to the Policy Owner."),
("7.7","Governing Law","Governed by the laws of Singapore. Disputes subject to Singapore court jurisdiction."),
("7.8","Policy Owners' Protection Scheme","Protected under the PPF Scheme administered by SDIC."),
],
'disability': [
("7.1","Entire Contract","This Policy, the Policy Schedule, Schedule of Benefits, application form, and endorsements constitute the entire disability income contract."),
("7.2","Offset Provision","Monthly Benefit is reduced by aggregate disability income from all other sources such that total income does not exceed one hundred percent (100%) of Pre-disability Earned Income."),
("7.3","Medical Examination","The Company may require independent medical examination at any time during claimed disability. Refusal entitles the Company to suspend or terminate the Monthly Benefit."),
("7.4","Rehabilitation Cooperation","The Insured shall cooperate with reasonable rehabilitation programmes. Unreasonable refusal entitles the Company to suspend the Monthly Benefit."),
("7.5","Misrepresentation","Material misrepresentation entitles the Company to void this Policy and deny all claims."),
("7.6","Free Look Period","Twenty-one (21) days from receipt to cancel for a full refund of Premiums paid."),
("7.7","Governing Law","Governed by the laws of Singapore. Disputes subject to Singapore court jurisdiction."),
("7.8","Policy Owners' Protection Scheme","Protected under the PPF Scheme administered by SDIC."),
],
}

CLAIMS_PROVISIONS = {
'life': [
("6.1","Notification","The Policy Owner or Beneficiary shall notify the Company in writing within thirty (30) days of the insured event. For TPD claims, notification must be made within thirty (30) days of disability onset."),
("6.2","Death Claim Documents","Required: (i) completed claim form; (ii) original death certificate; (iii) attending physician's medical report; (iv) police or coroner's report for accidental death; (v) claimant's identity document; (vi) bank account details."),
("6.3","TPD Claim Documents","Required: (i) completed claim form; (ii) specialist medical report certifying nature and permanency of disability; (iii) supporting diagnostic reports; (iv) proof of identity."),
("6.4","Assessment and Payment","The Company shall assess claims and communicate its decision within fourteen (14) working days of receipt of complete documentation. Approved claims are paid within fourteen (14) working days of the decision."),
("6.5","Fraudulent Claims","Submission of a false, exaggerated, or fraudulent claim entitles the Company to void this Policy, recover all benefits paid, and report the matter to the relevant authorities."),
],
'health': [
("6.1","Notification","The Insured shall notify the Company of planned Hospitalisation at least forty-eight (48) hours in advance, or within forty-eight (48) hours of emergency admission."),
("6.2","Required Documentation","Required: (i) completed claim form; (ii) original hospital bills and receipts; (iii) attending physician's discharge summary; (iv) laboratory and imaging reports; (v) surgeon's report for surgical claims; (vi) referral letter for specialist outpatient claims."),
("6.3","Submission Timeline","All claims must be submitted within ninety (90) days of discharge or the date of last outpatient treatment. Late claims may be rejected at the Company's discretion."),
("6.4","Assessment","The Company shall assess submitted claims within fourteen (14) working days of receipt of complete documentation and may require independent medical examination."),
("6.5","Direct Hospital Billing","Where the Insured is admitted to a participating Approved Hospital under the Company's direct billing arrangement, the Company shall settle Eligible Expenses directly with the hospital, subject to applicable limits and co-payment obligations."),
],
'critical_illness': [
("6.1","Notification","The Policy Owner or Insured shall notify the Company in writing within thirty (30) days of Diagnosis, providing sufficient preliminary information to enable the Company to begin assessment."),
("6.2","Required Documentation","Required: (i) completed CI claim form; (ii) specialist medical report confirming Diagnosis and clinical basis; (iii) histopathology report (cancer); (iv) ECG and biomarker results (heart attack); (v) neuroimaging and neurology assessment (stroke); (vi) nephrology reports and dialysis records (kidney failure); (vii) surgical reports (organ transplant)."),
("6.3","Survival Period Verification","The Company shall not process payment until expiry of the thirty (30) day Survival Period. The claimant shall provide specialist confirmation that the Insured has survived."),
("6.4","Independent Medical Examination","The Company may arrange independent examination by a Specialist at the Company's expense. Refusal may result in suspension or rejection of the claim."),
("6.5","Payment","Upon approval, the Critical Illness Benefit shall be paid within fourteen (14) working days by bank transfer to the designated account."),
],
'disability': [
("6.1","Notification","The Insured or Policy Owner shall notify the Company within thirty (30) days of disability onset, with a preliminary medical report from the attending physician."),
("6.2","Required Documentation","Required: (i) completed disability claim form; (ii) specialist medical report certifying nature, cause, and extent of disability; (iii) diagnostic reports and functional capacity evaluations; (iv) evidence of Pre-disability Earned Income for twelve (12) months; (v) proof of occupation."),
("6.3","Elimination Period Verification","No claim shall be processed until continuous Total Disability for the full ninety (90) day Elimination Period is established by medical evidence."),
("6.4","Ongoing Review","The Company shall conduct periodic review not less than every six (6) months, requiring: (i) updated specialist reports; (ii) independent medical examination; and (iii) evidence of rehabilitation participation."),
("6.5","Return to Work","The Insured shall notify the Company within seven (7) days of returning to any gainful employment. Failure may result in recovery of overpaid Monthly Benefit."),
],
}

def build_pdf(policy):
    pid   = policy['policy_id']
    ptype = policy['policy_type']
    pname = policy['policy_name']
    rng   = rng_for(pid)

    holder = policy.get('policyholder_name', 'Unknown')
    nric_r = rand_nric(rng)
    nric_m = mask(nric_r)
    dob    = rand_dob(rng)
    addr   = rand_addr(rng)
    occ    = rand_occ(rng)
    bene   = rng.choice(BENE_NAMES)
    rel    = rng.choice(RELS)
    sa     = policy['sum_assured']
    prem   = policy['premium_amount']
    freq   = policy['premium_frequency']
    start  = date.fromisoformat(policy['start_date'])
    end    = date.fromisoformat(policy['end_date'])
    status = policy['status'].upper()
    agid   = policy['agent_id']
    custid = policy['customer_id']
    ptype_d = ptype.replace('_', ' ').title()
    monthly_benefit = round(sa / 60, 2)

    issue_s  = start.strftime('%d %B %Y')
    end_s    = end.strftime('%d %B %Y')
    dob_s    = dob.strftime('%d %B %Y')
    today_s  = date.today().strftime('%d %B %Y')

    prod_desc = PRODUCT_DESCRIPTIONS.get(pname, ('A comprehensive insurance plan tailored to your protection needs.', '90 days', 'As stated in Policy Schedule', 'Standard benefits'))

    S = make_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=22*mm, leftMargin=22*mm,
        topMargin=20*mm, bottomMargin=20*mm)

    story = []
    txt   = []

    def HR(): story.append(HRFlowable(width='100%', thickness=1, color=BLACK, spaceAfter=3))
    def HRg(): story.append(HRFlowable(width='100%', thickness=0.5, color=RULE_GREY, spaceAfter=3))
    def SP(h=4): story.append(Spacer(1, h*mm))
    def P(text, style): story.append(Paragraph(text, S[style])); txt.append(text)
    def PB(): story.append(PageBreak())

    def row(l, v, l2='', v2=''):
        return [Paragraph(l, S['lbl']), Paragraph(str(v), S['val']),
                Paragraph(l2, S['lbl']), Paragraph(str(v2), S['val'])]

    # ── PAGE 1: HEADER + POLICY SCHEDULE ─────────────────────────────────────
    P("AIA Singapore Pte. Ltd.", 'co')
    SP(2)
    P("1 Raffles Quay, North Tower, Singapore 048583", 'co_sub')
    P("Reg. No. 202600001Z  |  MAS Licence No. LI-SIM-2026-001  |  Tel: 1800 248 0000  |  www.aia-s.com.sg", 'co_sub')
    SP(5)
    HR()
    SP(3)
    P(f"POLICY CONTRACT", 'doc_title')
    P(f"{pname.upper()}  |  {ptype_d} Insurance  |  Policy No: {pid}", 'doc_sub')
    HR()
    SP(4)

    P("SECTION 1 — POLICY SCHEDULE", 'sec')
    txt.append(f"SECTION 1 — POLICY SCHEDULE | Policy: {pid} | Type: {ptype_d} | Product: {pname}")

    rows = [
        row("Policy Number", pid, "Customer Reference", custid),
        row("Policy Type", ptype_d, "Plan / Product Name", pname),
        row("Policyholder / Life Assured", holder, "NRIC / FIN (Masked)", nric_m),
        row("Date of Birth", dob_s, "Occupation", occ),
        row("Residential Address", addr, "Agent ID", agid),
        row("Sum Assured", f"SGD {sa:,.2f}", "Premium", f"SGD {prem:,.2f} ({freq})"),
        row("Issue / Commencement Date", issue_s, "Expiry Date", end_s),
        row("Policy Status", status, "Currency", "Singapore Dollar (SGD)"),
    ]
    if ptype == 'disability':
        rows += [
            row("Monthly Benefit", f"SGD {monthly_benefit:,.2f}", "Elimination Period", "90 consecutive days"),
            row("Benefit Period", "To age 65", "Waiver of Premium", "Included"),
        ]
    if ptype == 'health':
        ded = min(3500, round(sa * 0.015))
        rows += [
            row("Annual Benefit Limit", f"SGD {sa:,.2f}", "Deductible", f"SGD {ded:,.2f} per Policy Year"),
            row("Co-insurance", "10% after Deductible", "MediShield Life Integrated", "Yes"),
        ]

    tbl = Table(rows, colWidths=[43*mm, 52*mm, 43*mm, 50*mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(0,-1), BG_GREY),
        ('BACKGROUND', (2,0),(2,-1), BG_GREY),
        ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0),(2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 8.5),
        ('GRID', (0,0),(-1,-1), 0.4, RULE_GREY),
        ('PADDING', (0,0),(-1,-1), 5),
        ('VALIGN', (0,0),(-1,-1), 'TOP'),
        ('BOX', (0,0),(-1,-1), 0.8, BLACK),
    ]))
    story.append(tbl)
    txt.append(f"Policyholder: {holder} | NRIC: {nric_m} | DOB: {dob_s} | Occupation: {occ} | Address: {addr}")
    txt.append(f"Sum Assured: SGD {sa:,.2f} | Premium: SGD {prem:,.2f} {freq} | Issue: {issue_s} | Expiry: {end_s} | Status: {status} | Agent: {agid}")

    SP(5)
    P("PRODUCT DESCRIPTION AND KEY FEATURES", 'subsec')
    P(prod_desc[0], 'body')
    SP(2)

    feat_rows = [
        [Paragraph("Waiting Period", S['lbl']), Paragraph(prod_desc[1], S['val']),
         Paragraph("Coverage Period", S['lbl']), Paragraph(prod_desc[2], S['val'])],
        [Paragraph("Key Differentiator", S['lbl']), Paragraph(prod_desc[3], S['val']),
         Paragraph("Policy Status", S['lbl']), Paragraph(status, S['val'])],
    ]
    ft = Table(feat_rows, colWidths=[38*mm, 57*mm, 38*mm, 55*mm])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(0,-1), BG_GREY),
        ('BACKGROUND', (2,0),(2,-1), BG_GREY),
        ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0),(2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 8.5),
        ('GRID', (0,0),(-1,-1), 0.4, RULE_GREY),
        ('PADDING', (0,0),(-1,-1), 5),
        ('BOX', (0,0),(-1,-1), 0.8, BLACK),
    ]))
    story.append(ft)

    SP(5)
    P("BENEFICIARY / NOMINEE DETAILS", 'subsec')
    bene_rows = [
        [Paragraph("Beneficiary Name", S['lbl']), Paragraph("Relationship", S['lbl']),
         Paragraph("Share of Benefits", S['lbl']), Paragraph("Nomination Type", S['lbl'])],
        [Paragraph(bene, S['val']), Paragraph(rel, S['val']),
         Paragraph("100%", S['val']), Paragraph("Revocable Nomination", S['val'])],
    ]
    bt = Table(bene_rows, colWidths=[52*mm, 42*mm, 42*mm, 52*mm])
    bt.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), DARK_GREY),
        ('TEXTCOLOR', (0,0),(-1,0), WHITE),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 8.5),
        ('GRID', (0,0),(-1,-1), 0.4, RULE_GREY),
        ('PADDING', (0,0),(-1,-1), 5),
        ('BOX', (0,0),(-1,-1), 0.8, BLACK),
    ]))
    story.append(bt)
    txt.append(f"Beneficiary: {bene} | Relationship: {rel} | Share: 100% | Nomination: Revocable")
    PB()

    # ── SECTION 2: DEFINITIONS ────────────────────────────────────────────────
    P("SECTION 2 — DEFINITIONS AND INTERPRETATION", 'sec')
    P("In this Policy, unless the context otherwise requires, the following terms shall have the meanings ascribed below. All definitions apply throughout this Policy, including the Policy Schedule and any endorsements.", 'body')
    SP(2)
    for term, meaning in DEFINITIONS.get(ptype, []):
        story.append(KeepTogether([
            Paragraph(f"<b>{term}</b>", S['clause']),
            Paragraph(meaning, S['sub']),
            Spacer(1, 2*mm),
        ]))
        txt.append(f"DEFINITION — {term}: {meaning}")
    PB()

    # ── SECTION 3: BENEFIT PROVISIONS ─────────────────────────────────────────
    P("SECTION 3 — BENEFIT PROVISIONS", 'sec')
    for cn, ct, cc in BENEFITS.get(ptype, []):
        story.append(KeepTogether([
            Paragraph(f"<b>Clause {cn} — {ct}</b>", S['subsec']),
            Paragraph(cc, S['clause']),
            Spacer(1, 3*mm),
        ]))
        txt.append(f"CLAUSE {cn} — {ct}: {cc}")
    PB()

    # ── SECTION 4: EXCLUSIONS ─────────────────────────────────────────────────
    P("SECTION 4 — EXCLUSIONS", 'sec')
    P("The Company shall not be liable to pay any benefit in respect of, or arising directly or indirectly from, any of the following:", 'body')
    SP(2)
    for i, excl in enumerate(EXCLUSIONS.get(ptype, []), 1):
        story.append(KeepTogether([
            Paragraph(f"<b>4.{i}</b>   {excl}", S['clause']),
            Spacer(1, 2.5*mm),
        ]))
        txt.append(f"EXCLUSION 4.{i}: {excl}")
    PB()

    # ── SECTION 5: PREMIUM PROVISIONS ─────────────────────────────────────────
    P("SECTION 5 — PREMIUM PROVISIONS", 'sec')
    for cn, ct, cc in [
        ("5.1","Premium Payment",f"The Policy Owner shall pay the Premium of SGD {prem:,.2f} on a {freq} basis, commencing on the Issue Date and thereafter on each Premium Due Date until the earlier of: (i) the Expiry Date; (ii) the death of the Insured; or (iii) termination of this Policy. Premiums are payable in advance."),
        ("5.2","Grace Period","A Grace Period of thirty (30) calendar days is allowed for payment of each Premium after the Premium Due Date, during which this Policy remains in force. If Premium remains unpaid after the Grace Period, this Policy shall lapse from the Premium Due Date on which default occurred."),
        ("5.3","Policy Lapse","If this Policy lapses due to non-payment, no benefits are payable for events occurring after the lapse date. The Policy Owner may apply for reinstatement within two (2) years of lapse, subject to underwriting and payment of outstanding Premiums with interest."),
        ("5.4","Reinstatement","A lapsed Policy may be reinstated upon: (i) written application within two (2) years of lapse; (ii) satisfactory evidence of insurability; and (iii) payment of outstanding Premiums with interest. All waiting periods recommence from the reinstatement date."),
        ("5.5","Premium Adjustment","The Company may adjust the Premium at each Policy Anniversary based on attained age, prevailing rates, and risk profile changes. Not less than thirty (30) days' written notice shall be given of any adjustment."),
    ]:
        story.append(KeepTogether([
            Paragraph(f"<b>Clause {cn} — {ct}</b>", S['subsec']),
            Paragraph(cc, S['clause']),
            Spacer(1, 3*mm),
        ]))
        txt.append(f"CLAUSE {cn} — {ct}: {cc}")
    PB()

    # ── SECTION 6: CLAIMS ─────────────────────────────────────────────────────
    P("SECTION 6 — CLAIMS PROVISIONS", 'sec')
    for cn, ct, cc in CLAIMS_PROVISIONS.get(ptype, []):
        story.append(KeepTogether([
            Paragraph(f"<b>Clause {cn} — {ct}</b>", S['subsec']),
            Paragraph(cc, S['clause']),
            Spacer(1, 3*mm),
        ]))
        txt.append(f"CLAUSE {cn} — {ct}: {cc}")
    PB()

    # ── SECTION 7: GENERAL PROVISIONS ─────────────────────────────────────────
    P("SECTION 7 — GENERAL PROVISIONS", 'sec')
    for cn, ct, cc in GENERAL_PROVISIONS.get(ptype, []):
        story.append(KeepTogether([
            Paragraph(f"<b>Clause {cn} — {ct}</b>", S['subsec']),
            Paragraph(cc, S['clause']),
            Spacer(1, 3*mm),
        ]))
        txt.append(f"CLAUSE {cn} — {ct}: {cc}")
    PB()

    # ── SECTION 8: ASSIGNMENT & SERVICING ─────────────────────────────────────
    P("SECTION 8 — ASSIGNMENT, NOMINATION, AND POLICY SERVICING", 'sec')
    for cn, ct, cc in [
        ("8.1","Assignment","The Policy Owner may assign this Policy by written notice to the Company in the prescribed form. Assignment takes effect only upon the Company's written acknowledgement."),
        ("8.2","Nomination",f"The Policy Owner may nominate or change the Beneficiary by written notice in prescribed form, subject to Section 49L of the Insurance Act 1966. Current nominated Beneficiary: {bene} ({rel}), 100% entitlement."),
        ("8.3","Policy Alterations","The Policy Owner may apply to alter this Policy, including Sum Assured, Premium frequency, or Beneficiary, subject to underwriting approval. No alteration is effective until confirmed in writing."),
        ("8.4","Duplicate Policy","Upon written application and payment of the prescribed fee, the Company may issue a duplicate Policy document. The original, if found, shall be void."),
        ("8.5","Currency and Payment",f"All Premiums and benefits are in SGD. Premiums may be paid by GIRO, credit card, cheque, or other methods accepted by the Company."),
        ("8.6","Communications","All notices shall be in writing and delivered to the parties at addresses in the Policy Schedule. Notices by post are deemed received two (2) business days after posting."),
    ]:
        story.append(KeepTogether([
            Paragraph(f"<b>Clause {cn} — {ct}</b>", S['subsec']),
            Paragraph(cc, S['clause']),
            Spacer(1, 3*mm),
        ]))
        txt.append(f"CLAUSE {cn} — {ct}: {cc}")
    PB()

    # ── SECTION 9: REGULATORY NOTICES ─────────────────────────────────────────
    P("SECTION 9 — REGULATORY NOTICES AND DECLARATIONS", 'sec')
    for cn, ct, cc in [
        ("9.1","MAS Regulatory Notice","This Policy is issued pursuant to the Insurance Act 1966 (Cap. 142) of Singapore and is subject to MAS regulations and guidelines. The Company is duly licensed by MAS to carry on insurance business in Singapore."),
        ("9.2","Policy Owners' Protection Scheme","This Policy is protected under the PPF Scheme administered by SDIC. Coverage is automatic. For information on coverage types and limits, contact the Company or visit www.sdic.org.sg."),
        ("9.3","Personal Data Protection","By accepting this Policy, the Policy Owner and Insured consent to the Company collecting, using, and disclosing personal data under the PDPA 2012 for: (i) policy administration; (ii) underwriting; (iii) claims processing; (iv) fraud detection; and (v) regulatory compliance."),
        ("9.4","Financial Advisers Act","This Policy was arranged through a Financial Adviser Representative licensed under the Financial Advisers Act (Cap. 110). The Policy Owner acknowledges receipt of required product disclosures including the Product Summary, Policy Illustration, and Key Information Sheet."),
        ("9.5","Duty of Disclosure","Pursuant to Section 25 of the Insurance Act 1966, the Policy Owner and Insured are under a duty to disclose all material facts, whether or not enquired about, prior to entering into this contract. Failure may entitle the Company to void this Policy."),
    ]:
        story.append(KeepTogether([
            Paragraph(f"<b>Clause {cn} — {ct}</b>", S['subsec']),
            Paragraph(cc, S['clause']),
            Spacer(1, 3*mm),
        ]))
        txt.append(f"CLAUSE {cn} — {ct}: {cc}")
    PB()

    # ── SECTION 10: SCHEDULE OF BENEFITS + EXECUTION ─────────────────────────
    P("SECTION 10 — SCHEDULE OF BENEFITS AND EXECUTION", 'sec')
    SP(2)
    P("SCHEDULE OF BENEFITS", 'subsec')

    if ptype == 'life':
        sb_rows = [
            [Paragraph("Benefit", S['lbl']), Paragraph("Trigger Event", S['lbl']),
             Paragraph("Amount Payable (SGD)", S['lbl']), Paragraph("Waiting Period", S['lbl'])],
            [Paragraph("Death Benefit", S['val']), Paragraph("Death of Insured", S['val']),
             Paragraph(f"{sa:,.2f}", S['val']), Paragraph("90 days", S['val'])],
            [Paragraph("Accidental Death Benefit", S['val']), Paragraph("Accidental death within 365 days", S['val']),
             Paragraph(f"{sa:,.2f} (additional)", S['val']), Paragraph("None", S['val'])],
            [Paragraph("TPD Benefit", S['val']), Paragraph("TPD before age 70", S['val']),
             Paragraph(f"{sa:,.2f}", S['val']), Paragraph("90 days", S['val'])],
        ]
    elif ptype == 'health':
        ded = min(3500, round(sa * 0.015))
        sb_rows = [
            [Paragraph("Benefit", S['lbl']), Paragraph("Annual Limit (SGD)", S['lbl']),
             Paragraph("Deductible (SGD)", S['lbl']), Paragraph("Co-insurance", S['lbl'])],
            [Paragraph("Hospitalisation", S['val']), Paragraph(f"{sa:,.2f}", S['val']),
             Paragraph(f"{ded:,.2f}", S['val']), Paragraph("10%", S['val'])],
            [Paragraph("Surgical Procedures", S['val']), Paragraph("Per MOH Table", S['val']),
             Paragraph(f"{ded:,.2f}", S['val']), Paragraph("10%", S['val'])],
            [Paragraph("Outpatient Specialist", S['val']), Paragraph(f"{min(5000,round(sa*0.05)):,.2f}", S['val']),
             Paragraph("Nil", S['val']), Paragraph("20%", S['val'])],
            [Paragraph("Emergency Treatment", S['val']), Paragraph(f"{min(3000,round(sa*0.03)):,.2f}", S['val']),
             Paragraph("Nil", S['val']), Paragraph("10%", S['val'])],
        ]
    elif ptype == 'critical_illness':
        sb_rows = [
            [Paragraph("Covered Condition", S['lbl']), Paragraph("Waiting Period", S['lbl']),
             Paragraph("Survival Period", S['lbl']), Paragraph("Lump Sum Benefit (SGD)", S['lbl'])],
            [Paragraph("Cancer", S['val']), Paragraph("90 days", S['val']),
             Paragraph("30 days", S['val']), Paragraph(f"{sa:,.2f}", S['val'])],
            [Paragraph("Heart Attack", S['val']), Paragraph("90 days", S['val']),
             Paragraph("30 days", S['val']), Paragraph(f"{sa:,.2f}", S['val'])],
            [Paragraph("Stroke", S['val']), Paragraph("90 days", S['val']),
             Paragraph("30 days", S['val']), Paragraph(f"{sa:,.2f}", S['val'])],
            [Paragraph("Kidney Failure", S['val']), Paragraph("90 days", S['val']),
             Paragraph("30 days", S['val']), Paragraph(f"{sa:,.2f}", S['val'])],
            [Paragraph("Major Organ Transplant", S['val']), Paragraph("90 days", S['val']),
             Paragraph("30 days", S['val']), Paragraph(f"{sa:,.2f}", S['val'])],
        ]
    else:
        sb_rows = [
            [Paragraph("Benefit", S['lbl']), Paragraph("Trigger", S['lbl']),
             Paragraph("Amount", S['lbl']), Paragraph("Duration", S['lbl'])],
            [Paragraph("Monthly Benefit", S['val']),
             Paragraph("Total Disability after 90-day Elimination Period", S['val']),
             Paragraph(f"SGD {monthly_benefit:,.2f}/month", S['val']),
             Paragraph("To age 65", S['val'])],
            [Paragraph("Partial Disability Benefit", S['val']),
             Paragraph("Partial Disability after Total Disability", S['val']),
             Paragraph("Pro-rated Monthly Benefit", S['val']),
             Paragraph("Up to 6 months", S['val'])],
            [Paragraph("TPD Lump Sum", S['val']),
             Paragraph("Total Permanent Disability", S['val']),
             Paragraph(f"SGD {monthly_benefit*12:,.2f}", S['val']),
             Paragraph("Once", S['val'])],
            [Paragraph("Rehabilitation Benefit", S['val']),
             Paragraph("Approved rehabilitation programme", S['val']),
             Paragraph("50% of Monthly Benefit", S['val']),
             Paragraph("Up to 12 months", S['val'])],
            [Paragraph("Waiver of Premium", S['val']),
             Paragraph("During Total Disability", S['val']),
             Paragraph("100% of premium waived", S['val']),
             Paragraph("Until recovery or age 65", S['val'])],
        ]

    sbt = Table(sb_rows, colWidths=[47*mm, 52*mm, 42*mm, 47*mm])
    sbt.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), DARK_GREY),
        ('TEXTCOLOR', (0,0),(-1,0), WHITE),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 8.5),
        ('GRID', (0,0),(-1,-1), 0.4, RULE_GREY),
        ('PADDING', (0,0),(-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [WHITE, BG_GREY]),
        ('BOX', (0,0),(-1,-1), 0.8, BLACK),
    ]))
    story.append(sbt)
    txt.append(f"Schedule of Benefits: {ptype_d} | Sum Assured SGD {sa:,.2f}")

    SP(6)
    HRg()
    P("POLICY OWNER DECLARATION AND EXECUTION", 'subsec')
    SP(2)
    P(f"I, <b>{holder}</b> (NRIC: {nric_m}), as Policy Owner, hereby confirm that:", 'body')
    for decl in [
        "I have read, understood, and agreed to all terms and conditions of this Policy Contract.",
        "All statements in the application are true, complete, and accurate to the best of my knowledge.",
        "I have received the Product Summary, Policy Illustration, and Key Information Sheet.",
        "I understand this Policy is a legally binding contract with AIA Singapore Pte. Ltd.",
        f"I nominate {bene} ({rel}) as Beneficiary under this Policy.",
    ]:
        story.append(Paragraph(f"&#x2022;  {decl}", S['clause']))
        txt.append(decl)

    SP(6)
    sig_rows = [
        [Paragraph("Policy Owner Signature", S['lbl']), Paragraph("Date", S['lbl']),
         Paragraph("Financial Adviser / Witness", S['lbl']), Paragraph("Date", S['lbl'])],
        [Paragraph("___________________________", S['val']), Paragraph(today_s, S['val']),
         Paragraph("___________________________", S['val']), Paragraph(today_s, S['val'])],
        [Paragraph(holder, S['val']), Paragraph("", S['val']),
         Paragraph(f"Agent ID: {agid}", S['val']), Paragraph("", S['val'])],
    ]
    st = Table(sig_rows, colWidths=[47*mm, 42*mm, 47*mm, 52*mm])
    st.setStyle(TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),8.5), ('PADDING',(0,0),(-1,-1),5),
        ('GRID',(0,0),(-1,-1),0.4,RULE_GREY),
        ('BACKGROUND',(0,0),(-1,0),BG_GREY),
        ('BOX',(0,0),(-1,-1),0.8,BLACK),
    ]))
    story.append(st)
    txt.append(f"Signed: {holder} | Agent: {agid} | Date: {today_s}")

    SP(5)
    HRg()
    for line in [
        "FOR AND ON BEHALF OF AIA SINGAPORE PTE. LTD.",
        "___________________________          ___________________________",
        "Authorised Signatory                          Authorised Signatory",
        "Chief Executive Officer                       Chief Risk Officer",
        " ",
        f"Policy Issued: {today_s}  |  Policy No: {pid}  |  Customer Ref: {custid}",
        "AIA Singapore Pte. Ltd.  |  1 Raffles Quay, North Tower, Singapore 048583",
        "Tel: 1800 248 0000  |  Email: service@aia-s.com.sg  |  www.aia-s.com.sg",
        "Licensed by MAS. Protected by SDIC under the Policy Owners' Protection Scheme.",
    ]:
        P(line, 'footer')

    doc.build(story)
    pdf_bytes = buf.getvalue()
    policy_text = '\n'.join(txt)

    # Summary
    summary = (
        f"Policy {pid} — {pname} ({ptype_d}). "
        f"Policyholder: {holder} (NRIC: {nric_m}, DOB: {dob_s}, Occupation: {occ}). "
        f"Sum Assured: SGD {sa:,.2f}. Premium: SGD {prem:,.2f} {freq}. "
        f"Coverage: {issue_s} to {end_s}. Status: {status}. Agent: {agid}. "
        f"Beneficiary: {bene} ({rel}, 100%). "
        f"Product: {prod_desc[0]} "
    )
    if ptype == 'life':
        summary += (f"Death Benefit SGD {sa:,.2f}; Accidental Death additional SGD {sa:,.2f}; TPD SGD {sa:,.2f}. "
                    "Waiting period 90 days. Suicide exclusion 1 year. "
                    "Exclusions: pre-existing conditions, self-inflicted injury, war, criminal acts.")
    elif ptype == 'health':
        ded = min(3500, round(sa*0.015))
        summary += (f"Hospitalisation up to SGD {sa:,.2f}/year; Deductible SGD {ded:,.2f}; Co-insurance 10%. "
                    "Waiting period 30 days for sickness. MediShield Life integrated. "
                    "Exclusions: pre-existing conditions, cosmetic, pregnancy, psychiatric.")
    elif ptype == 'critical_illness':
        summary += (f"Covers Cancer, Heart Attack, Stroke, Kidney Failure, Major Organ Transplant. "
                    f"Lump sum SGD {sa:,.2f} on diagnosis. Waiting period 90 days. Survival period 30 days. "
                    "Exclusions: pre-existing conditions, carcinoma-in-situ, TIAs, acute renal failure.")
    else:
        summary += (f"Monthly Benefit SGD {monthly_benefit:,.2f}/month after 90-day elimination period. "
                    f"TPD lump sum SGD {monthly_benefit*12:,.2f}. Benefit period to age 65. "
                    "Exclusions: pre-existing conditions, psychiatric, self-inflicted injury.")

    return pdf_bytes, policy_text, summary

print("PDF builder v2 loaded.")

# ── UPLOAD RUNNER ─────────────────────────────────────────────────────────────
import os, sys
from supabase import create_client
from dotenv import load_dotenv
from pypdf import PdfReader

def run():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY not set in .env")
        sys.exit(1)

    sb = create_client(url, key)

    print("Fetching policies...")
    policies = sb.table('policies').select('*').execute().data
    print(f"Found {len(policies)} policies\n")

    success, failed = 0, []

    for i, policy in enumerate(policies, 1):
        pid   = policy['policy_id']
        ptype = policy['policy_type']
        name  = policy.get('policyholder_name', '?')
        print(f"[{i:04d}/{len(policies)}] {pid} ({ptype}) — {name}...", end=' ', flush=True)

        try:
            pdf_bytes, policy_text, summary = build_pdf(policy)
            pages = len(PdfReader(io.BytesIO(pdf_bytes)).pages)

            file_path = f"policies/{pid}.pdf"
            sb.storage.from_('policy-documents').upload(
                path=file_path,
                file=pdf_bytes,
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            pdf_url = sb.storage.from_('policy-documents').get_public_url(file_path)

            sb.table('policies').update({
                'pdf_url': pdf_url,
                'policy_text': policy_text,
                'policy_summary': summary,
            }).eq('policy_id', pid).execute()

            print(f"OK ({pages}pp, {len(pdf_bytes):,}b)")
            success += 1

        except Exception as e:
            print(f"FAILED — {e}")
            failed.append(pid)

    print(f"\n{'='*60}")
    print(f"Complete: {success}/{len(policies)} succeeded.")
    if failed:
        print(f"Failed IDs: {failed}")

if __name__ == '__main__':
    run()