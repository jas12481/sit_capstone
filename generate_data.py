import random
from datetime import date, timedelta
from faker import Faker
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

fake = Faker('en_US')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ── PRODUCTS ──────────────────────────────────────────────────────────────────

PRODUCTS = {
    'life': [
        {'name': 'AIA LifeGuard Essential',    'sa': (100000, 300000),  'prem': (50, 150)},
        {'name': 'AIA LifeGuard Plus',          'sa': (200000, 500000),  'prem': (120, 300)},
        {'name': 'AIA LifeGuard Premier',       'sa': (400000, 700000),  'prem': (250, 550)},
        {'name': 'AIA SecureLife 300',          'sa': (250000, 400000),  'prem': (150, 350)},
        {'name': 'AIA SecureLife 600',          'sa': (500000, 800000),  'prem': (350, 700)},
        {'name': 'AIA SecureLife Platinum',     'sa': (750000, 2000000), 'prem': (500, 1500)},
        {'name': 'AIA WholeCover Basic',        'sa': (150000, 350000),  'prem': (200, 500)},
        {'name': 'AIA WholeCover Premier',      'sa': (300000, 600000),  'prem': (400, 900)},
        {'name': 'AIA FamilyShield Income',     'sa': (300000, 600000),  'prem': (180, 400)},
        {'name': 'AIA MortgageGuard',           'sa': (200000, 800000),  'prem': (100, 400)},
        {'name': 'AIA SeniorGuard 65',          'sa': (50000, 200000),   'prem': (300, 800)},
        {'name': 'AIA BusinessGuard Term',      'sa': (500000, 2000000), 'prem': (400, 1200)},
        {'name': 'AIA EndowSave 20',            'sa': (100000, 300000),  'prem': (400, 900)},
        {'name': 'AIA EndowSave 25',            'sa': (150000, 400000),  'prem': (350, 800)},
        {'name': 'AIA ConvertTerm Plus',        'sa': (200000, 600000),  'prem': (100, 350)},
    ],
    'health': [
        {'name': 'AIA MediShield Basic',        'sa': (20000, 50000),    'prem': (80, 150)},
        {'name': 'AIA MediShield Standard',     'sa': (50000, 100000),   'prem': (120, 250)},
        {'name': 'AIA MediShield Gold',         'sa': (100000, 200000),  'prem': (200, 400)},
        {'name': 'AIA MediShield Gold Max',     'sa': (200000, 400000),  'prem': (300, 600)},
        {'name': 'AIA MediShield Platinum',     'sa': (400000, 1000000), 'prem': (500, 1200)},
        {'name': 'AIA HealthPlus Essential',    'sa': (30000, 80000),    'prem': (100, 200)},
        {'name': 'AIA HealthPlus Comprehensive','sa': (80000, 200000),   'prem': (200, 450)},
        {'name': 'AIA HealthPlus Premier',      'sa': (250000, 500000),  'prem': (350, 700)},
        {'name': 'AIA CareShield Basic',        'sa': (50000, 100000),   'prem': (80, 180)},
        {'name': 'AIA CareShield Family',       'sa': (100000, 250000),  'prem': (180, 380)},
        {'name': 'AIA CancerCare Protect',      'sa': (100000, 300000),  'prem': (150, 350)},
        {'name': 'AIA MaternaCare',             'sa': (20000, 60000),    'prem': (120, 250)},
        {'name': 'AIA SeniorCare Shield',       'sa': (50000, 150000),   'prem': (400, 900)},
        {'name': 'AIA GlobalCare Elite',        'sa': (500000, 2000000), 'prem': (800, 2000)},
        {'name': 'AIA WellnessPlus Rider',      'sa': (5000, 15000),     'prem': (50, 100)},
    ],
    'critical_illness': [
        {'name': 'AIA CI Essential 5',          'sa': (50000, 100000),   'prem': (80, 180)},
        {'name': 'AIA CI Protect 10',           'sa': (100000, 200000),  'prem': (120, 280)},
        {'name': 'AIA CI Protect 36',           'sa': (150000, 300000),  'prem': (200, 450)},
        {'name': 'AIA CI Protect 53',           'sa': (200000, 400000),  'prem': (300, 650)},
        {'name': 'AIA CI MultiClaim',           'sa': (200000, 500000),  'prem': (350, 800)},
        {'name': 'AIA EarlyCI Basic',           'sa': (100000, 250000),  'prem': (150, 350)},
        {'name': 'AIA EarlyCI Premier',         'sa': (250000, 500000),  'prem': (300, 700)},
        {'name': 'AIA CancerGuard Plus',        'sa': (100000, 300000),  'prem': (100, 250)},
        {'name': 'AIA HeartGuard Plus',         'sa': (100000, 300000),  'prem': (120, 280)},
        {'name': 'AIA CI Monthly Income',       'sa': (50000, 150000),   'prem': (150, 350)},
        {'name': 'AIA CI Protect 360',          'sa': (150000, 400000),  'prem': (250, 600)},
        {'name': 'AIA SeniorCI Cover',          'sa': (50000, 150000),   'prem': (400, 900)},
        {'name': 'AIA CI FamilyCare',           'sa': (100000, 300000),  'prem': (180, 400)},
        {'name': 'AIA CI BusinessGuard',        'sa': (300000, 1000000), 'prem': (400, 1000)},
        {'name': 'AIA DreadDisease Premier',    'sa': (500000, 2000000), 'prem': (600, 1800)},
    ],
    'disability': [
        {'name': 'AIA DisabilityGuard Basic',   'sa': (24000, 60000),    'prem': (80, 180)},
        {'name': 'AIA DisabilityGuard Plus',    'sa': (36000, 96000),    'prem': (120, 280)},
        {'name': 'AIA DisabilityGuard Premier', 'sa': (60000, 180000),   'prem': (200, 500)},
        {'name': 'AIA IncomeShield Basic',      'sa': (18000, 48000),    'prem': (60, 140)},
        {'name': 'AIA IncomeShield Plus',       'sa': (36000, 84000),    'prem': (100, 240)},
        {'name': 'AIA IncomeShield Premier',    'sa': (48000, 120000),   'prem': (140, 320)},
        {'name': 'AIA TotalCover Disability',   'sa': (48000, 120000),   'prem': (150, 350)},
        {'name': 'AIA OccupationProtect',       'sa': (24000, 72000),    'prem': (100, 250)},
        {'name': 'AIA ExecutiveDisability',     'sa': (120000, 360000),  'prem': (400, 1000)},
        {'name': 'AIA FreelanceShield',         'sa': (24000, 72000),    'prem': (100, 220)},
        {'name': 'AIA AccidentDisability',      'sa': (24000, 60000),    'prem': (40, 100)},
        {'name': 'AIA RehabPlus Disability',    'sa': (36000, 96000),    'prem': (120, 280)},
        {'name': 'AIA PartialDisability Cover', 'sa': (24000, 72000),    'prem': (80, 200)},
        {'name': 'AIA SeniorDisability Shield', 'sa': (18000, 48000),    'prem': (300, 700)},
        {'name': 'AIA GroupDisability SME',     'sa': (24000, 84000),    'prem': (60, 160)},
    ],
}

CLAIM_CATEGORIES = {
    'life': ['death', 'accidental_death', 'total_permanent_disability'],
    'health': ['hospitalisation', 'surgical', 'outpatient', 'emergency'],
    'critical_illness': ['cancer', 'heart_attack', 'stroke', 'kidney_failure', 'major_organ_transplant'],
    'disability': ['total_temporary_disability', 'total_permanent_disability', 'partial_permanent_disability', 'occupational_disability'],
}

POLICY_TYPES = ['life', 'health', 'critical_illness', 'disability']

CLAIM_STATUS_POOL = ['approved', 'approved', 'approved', 'pending', 'pending', 'under_review', 'rejected']

OFFICERS = [
    'Sarah Tan', 'Michael Lim', 'Priya Nair', 'David Wong',
    'Jessica Koh', 'Rahul Sharma', 'Emily Chen', 'James Lee',
    'Nurul Huda', 'Bernard Goh', 'Kavitha Pillai', 'Marcus Teo',
]

POLICYHOLDER_NAMES = [
    'Tan Wei Ming', 'Lim Hui Shan', 'Priya d/o Subramaniam', 'Muhammad Farid Bin Hassan',
    'Wong Siew Ling', 'Ng Boon Huat', 'Kavitha d/o Krishnamurthy', 'Ismail Bin Ibrahim',
    'Chen Xiao Ming', 'Nurul Ain Binte Yusof', 'Ravi s/o Suppiah', 'Goh Kok Wah',
    'Lee Chee Keong', 'Suresh Nair s/o Krishnan', 'Chua Swee Lan', 'Farid Bin Osman',
    'Zhang Wei', 'Deepa d/o Nair', 'Ong Bak Cheng', 'Hafiz Bin Ahmad',
    'Liu Yang', 'Rajesh Kumar s/o Rajan', 'Lim Bee Hwa', 'Zainab Binte Mohamed',
    'Tan Ah Kow', 'Wang Fang', 'Siti Nurbaya Binte Salim', 'Govindasamy s/o Pillai',
    'Tan Siew Hua', 'Mohamed Rizal Bin Hamid', 'Loh Pei Shan', 'Anand s/o Krishnan',
    'Chong Mei Ling', 'Syafiq Bin Zulkifli', 'Vasantha d/o Murugasen', 'Koh Boon Seng',
    'Goh Cheng Huat', 'Malathi d/o Rajan', 'Abdul Razak Bin Salleh', 'Yeo Swee Keng',
    'Nirmala d/o Suppiah', 'Lim Choon Kiat', 'Rohani Binte Kassim', 'Teo Kok Leong',
    'Shamala d/o Gopal', 'Hassan Bin Yusoff', 'Chia Boon Lay', 'Punitha d/o Arumugam',
    'Mazlan Bin Othman', 'Aisha Binte Rashid', 'Tan Boon Kiat', 'Lim Swee Eng',
    'Noor Hidayah Binte Ramli', 'Jayakumar s/o Pillai', 'Tan Li Fen', 'Wong Ah Kow',
    'Rajeswari d/o Murugan', 'Fadzillah Binte Yusof', 'Ong Wei Liang', 'Selvam s/o Rajoo',
    'Mdm Koh Siew Geok', 'Nazrul Bin Nordin', 'Lim Kah Wai', 'Ng Swee Huat',
    'Indra d/o Ramasamy', 'Azman Bin Kassim', 'Tan Cher Ling', 'Ho Boon Seng',
    'Devi d/o Krishnan', 'Rosli Bin Abdullah', 'Chua Ah Lian', 'Mohan s/o Perumal',
    'Yap Siew Lian', 'Samsul Bin Bahari', 'Leong Mei Kuen', 'Krishnan s/o Nair',
    'Mdm Tan Bee Bee', 'Ridhwan Bin Hamdan', 'Sim Poh Choo', 'Balakrishnan s/o Pillai',
    'Nadia Binte Ismail', 'Tan Keng Huat', 'Lee Siew Ling', 'Fauzi Bin Rahman',
    'Geeta d/o Sharma', 'Chia Teck Huat', 'Norashikin Binte Ahmad', 'Lim Ah Moi',
    'Vengadasalam s/o Raju', 'Zainal Bin Othman', 'Tan Poh Choo', 'Rajan s/o Pillai',
    'Zulaikha Binte Osman', 'Ang Boon Huat', 'Hemavathy d/o Gopal', 'Hairul Bin Hamzah',
    'Poh Swee Eng', 'Subramaniam s/o Pillai', 'Junainah Binte Rashid', 'Wee Boon Keng',
]

def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_policies(n=1000):
    policies = []
    counters = {t: 1 for t in POLICY_TYPES}
    prefix_map = {'life': 'LI', 'health': 'HE', 'critical_illness': 'CI', 'disability': 'DI'}

    names_pool = POLICYHOLDER_NAMES * (n // len(POLICYHOLDER_NAMES) + 2)
    random.shuffle(names_pool)

    for i in range(n):
        ptype = POLICY_TYPES[i % 4]
        product = random.choice(PRODUCTS[ptype])
        sa_min, sa_max = product['sa']
        prem_min, prem_max = product['prem']

        sa = round(random.randint(sa_min, sa_max) / 1000) * 1000
        prem = round(random.uniform(prem_min, prem_max), 2)
        start = random_date(date(2015, 1, 1), date(2024, 12, 31))
        end = start + timedelta(days=365 * random.randint(10, 35))
        status = random.choices(
            ['active', 'lapsed', 'terminated'],
            weights=[85, 10, 5], k=1
        )[0]

        policy_id = f"POL-{prefix_map[ptype]}-{counters[ptype]:04d}"
        counters[ptype] += 1

        policies.append({
            'policy_id': policy_id,
            'customer_id': f"CUST-{(i+1):04d}",
            'agent_id': f"AGT-{random.randint(1, 50):03d}",
            'policy_type': ptype,
            'policy_name': product['name'],
            'policyholder_name': names_pool[i],
            'sum_assured': sa,
            'premium_amount': prem,
            'premium_frequency': random.choice(['monthly', 'quarterly', 'annual']),
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'status': status,
            'pdf_url': None,
            'policy_text': None,
            'policy_summary': None,
            'created_at': start.isoformat(),
        })

    return policies

def generate_claims(policies):
    claims = []
    claim_counter = 1

    # Type-specific claim frequency based on Singapore insurance statistics:
    # Health: avg ~4/policy (MOH: 40yr old hospitalised 1-2x per 20yrs; IP riders 1.4x more likely to claim)
    # Disability: avg ~1/policy (temporary disability can recur; LIA 2023 data)
    # Critical illness: avg ~0.5/policy (1 in 4 Singaporeans develop CI; one-time payout)
    # Life: avg ~0.3/policy (death/TPD are rare lifetime events)
    CLAIM_WEIGHTS = {
        'health':           [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'disability':       [0, 0, 1, 1, 1, 2, 2, 3, 3],
        'critical_illness': [0, 0, 0, 0, 0, 0, 1, 1, 1],
        'life':             [0, 0, 0, 0, 0, 0, 0, 1, 1],
    }

    for policy in policies:
        ptype = policy['policy_type']
        n_claims = random.choice(CLAIM_WEIGHTS[ptype])
        start = date.fromisoformat(policy['start_date'])
        end = date.fromisoformat(policy['end_date'])
        sa = policy['sum_assured']

        for _ in range(n_claims):
            waiting = 30 if ptype == 'health' else 90
            earliest = start + timedelta(days=waiting)
            latest = min(end, date(2025, 12, 31))
            if earliest >= latest:
                continue

            incident = random_date(earliest, latest)
            claim_date = incident + timedelta(days=random.randint(1, 60))
            category = random.choice(CLAIM_CATEGORIES[ptype])
            status = random.choice(CLAIM_STATUS_POOL)
            claim_amount = round(random.uniform(sa * 0.05, sa * 0.95), 2)

            approved_amount = None
            payment_date = None
            rejection_reason = None

            if status == 'approved':
                approved_amount = claim_amount
                payment_date = (claim_date + timedelta(days=random.randint(14, 45))).isoformat()
            elif status == 'rejected':
                rejection_reason = random.choice([
                    'Claim submitted within waiting period',
                    'Policy was lapsed at time of incident',
                    'Claim amount exceeds sum assured',
                    'Condition is a pre-existing illness not declared at underwriting',
                    'Insufficient supporting documents provided',
                    'Incident does not fall within policy coverage period',
                    'Diagnosis does not meet the clinical criteria defined in the policy',
                    'Survival period of 30 days not satisfied',
                ])

            claims.append({
                'claim_id': f"CLM-{claim_counter:04d}",
                'policy_id': policy['policy_id'],
                'customer_id': policy['customer_id'],
                'claim_type': ptype,
                'claim_category': category,
                'claim_date': claim_date.isoformat(),
                'incident_date': incident.isoformat(),
                'claim_amount': claim_amount,
                'approved_amount': approved_amount,
                'payment_date': payment_date,
                'status': status,
                'rejection_reason': rejection_reason,
                'assigned_officer': random.choice(OFFICERS),
                'notes': fake.sentence(nb_words=12),
                'created_at': claim_date.isoformat(),
            })
            claim_counter += 1

    return claims

def insert_policies(policies):
    print(f"Inserting {len(policies)} policies...")
    for i in range(0, len(policies), 100):
        batch = policies[i:i+100]
        supabase.table('policies').insert(batch).execute()
        print(f"  Batch {i//100+1}: {len(batch)} rows")
    print(f"Done — {len(policies)} policies inserted")

def insert_claims(claims):
    print(f"\nInserting {len(claims)} claims...")
    for i in range(0, len(claims), 100):
        batch = claims[i:i+100]
        supabase.table('claims').insert(batch).execute()
        print(f"  Batch {i//100+1}: {len(batch)} rows")
    print(f"Done — {len(claims)} claims inserted")

if __name__ == '__main__':
    random.seed(42)
    print("Generating 1000 policies...\n")
    policies = generate_policies(1000)
    insert_policies(policies)

    print("\nGenerating claims with realistic distribution...")
    claims = generate_claims(policies)
    insert_claims(claims)

    print(f"\n{'='*50}")
    print(f"Complete!")
    print(f"  Policies: {len(policies)}")
    print(f"  Claims:   {len(claims)}")