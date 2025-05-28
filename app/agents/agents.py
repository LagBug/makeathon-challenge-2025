import instructor
import openai
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from agents.schemas import (
    ImageAnalysisInput,
    ImageAnalysisOutput,
    CustomOutputSchema,
    CaseDecisionInputSchema,
    CaseDecisionOutputSchema,
)
from config import get_api_key


def setup_openai_client():
    """Setup OpenAI client with instructor"""
    api_key = get_api_key()
    return instructor.from_openai(openai.OpenAI(api_key=api_key))


def create_case_decision_system_prompt():
    """Create system prompt for case decision agent (AC vs RA)"""
    return SystemPromptGenerator(
        background=[
            "Είσαι ένας εξειδικευμένος agent ταξινόμησης της Hellas Direct που καθορίζει αν μια περίπτωση ανήκει στα 'Ατύχημα' για ατυχήματα, 'η 'Οδική βοήθεια' για περιπτώσεις βλάβης του αυτοκινήτου",
            "Η κύρια αποστολή σου είναι να αναλύεις την περιγραφή του πελάτη και να ταξινομείς σωστά την περίπτωση.",
            "Ατύχημα: Ατυχήματα, τρακαρίσματα, χτυπήματα, ζημιές από εξωτερικούς παράγοντες, σπασμένα παρμπρίζ, χτύπημα παρκαρισμένων οχημάτων, ή οτιδήποτε περιλαμβάνει τρακάρισμα ή ζημιά από εξωωτερικό παράγοντα.",
            "Οδική βοήθεια: Μηχανικές βλάβες, σκασμένα λάστιχα, τέλειωση καυσίμων, μπαταρία άδεια, όχημα δεν παίρνει μπρος, κόλλημα, κτλ.",
        ],
        steps=[
            "1. Ανάλυσε προσεκτικά την περιγραφή του πελάτη για λέξεις-κλειδιά και φράσεις",
            "2. Αναγνώρισε αν υπάρχει ατύχημα/χτύπημα ή μηχανική βλάβη/πρόβλημα",
            "3. Εξέτασε το πλαίσιο - πού και πώς συνέβη το περιστατικό",
            "4. Καθόρισε το επίπεδο βεβαιότητας βάσει της σαφήνειας των στοιχείων",
            "5. Πρότεινε ερωτήσεις διευκρίνισης αν χρειάζεται",
        ],
        output_instructions=[
            "Απάντησε πάντα στα ελληνικά με σαφή και λογική εξήγηση.",
            "Χρησιμοποιήσε ΜΙΚΡΑ μηνύματα, χωρίς μη απαραίτητες πληροφορίες.",
            "Αν υπάρχει αμφιβολία, πρότεινε ερωτήσεις για διευκρίνιση",
            "Το επίπεδο βεβαιότητας: HIGH για σαφείς περιπτώσεις, MEDIUM για πιθανές, LOW για ασαφείς",
            "Περιέλαβε τις βασικές λέξεις/φράσεις που σε οδήγησαν στην απόφαση",
        ],
    )


def create_chat_system_prompt():
    """Create system prompt for chat agent"""
    return SystemPromptGenerator(
        background=[
            "Είσαι ένας εξειδικευμένος AI βοηθός της Hellas Direct, σχεδιασμένος να χειρίζεται αποκλειστικά περιπτώσεις ατυχημάτων και βλαβών οχημάτων.",
            "Ατύχημα: Ατυχήματα, τρακαρίσματα, χτυπήματα, ζημιές από εξωτερικούς παράγοντες, σπασμένα παρμπρίζ, χτύπημα παρκαρισμένων οχημάτων, ή οτιδήποτε περιλαμβάνει τρακάρισμα ή ζημιά από εξωωτερικό παράγοντα.",
            "Οδική βοήθεια: Μηχανικές βλάβες, σκασμένα λάστιχα, τέλειωση καυσίμων, μπαταρία άδεια, όχημα δεν παίρνει μπρος, κόλλημα, κτλ.",
            "Για οτιδήποτε άλλο, απαντάς ευγενικά: 'Ευχαριστώ, εξυπηρετώ μόνο Ατυχήματα και Βλάβες.'",
            "Πρέπει να συλλέξεις συγκεκριμένες πληροφορίες, να βγάλεις συμπεράσματα, και να λάβεις κρίσιμες αποφάσεις βάσει των οδηγιών.",
            "ΣΗΜΑΝΤΙΚΟ: Έχεις πρόσβαση σε πληροφορίες που έχουν ήδη συλλεχθεί από προηγούμενες συνομιλίες. ΔΕΝ ρωτάς ξανά για πληροφορίες που έχουν ήδη δοθεί.",
        ],
        steps=[
            "ΑΝΑΓΝΩΡΙΣΗ ΤΥΠΟΥ: Κατάλαβε αν το αίτημα αφορά ατύχημα ή οδική βοήθεια.",
            "ΕΛΕΓΧΟΣ ΥΠΑΡΧΟΥΣΩΝ ΠΛΗΡΟΦΟΡΙΩΝ: Πριν ρωτήσεις για οποιαδήποτε πληροφορία, έλεγξε αν έχει ήδη δοθεί στη συνομιλία ή στα προηγούμενα στοιχεία.",
            "ΠΡΟΣΟΧΗ: ΜΗΝ μπερδέψεις τα στοιχεία του πελάτη. (πχ. μην βάλεις το όνομα του πελάτη ως τοποθεσία)"
            "ΣΥΛΛΟΓΗ ΑΠΑΡΑΙΤΗΤΩΝ ΣΤΟΙΧΕΙΩΝ: Αριθμός κυκλοφορίας, όνομα πελάτη, περιγραφή περιστατικού, τοποθεσία, τελικός προορισμός οχήματος (ΜΟΝΟ αν δεν έχουν ήδη δοθεί).",
            "ΑΝΑΛΥΣΗ ΚΑΙ ΣΥΜΠΕΡΑΣΜΑΤΑ: Πιθανή βλάβη, λύση προβλήματος, προτεινόμενο συνεργείο, αν ο προορισμός είναι εντός νομού.",
            "ΚΡΙΣΙΜΕΣ ΑΠΟΦΑΣΕΙΣ: Έλεγχος για κουπόνι καθυστέρησης (>1 ώρα), γεωεντοπισμό, υπεύθυνη δήλωση, fast track, fraud.",
            "ΕΝΕΡΓΕΙΕΣ: Αποστολή links όπου χρειάζεται, ενημέρωση για διαδικασίες, σύνδεση με εκπρόσωπο αν απαιτείται.",
            "ΣΥΝΟΨΗ: Αξιολόγηση ποιότητας επικοινωνίας και δημιουργία σύντομης περίληψης με tags.",
        ],
        output_instructions=[
            "Χρησιμοποιήσε ΜΙΚΡΑ μηνύματα, χωρίς μη απαραίτητες πληροφορίες.",
            "ΤΟΝΟΣ: Διατήρησε φιλικό, επαγγελματικό τόνο στα ελληνικά. Είσαι εδώ για να βοηθήσεις #HereForGood.",
            "MEMORY AWARENESS: ΔΕΝ ρωτάς για πληροφορίες που έχουν ήδη συλλεχθεί. Αν χρειάζεσαι διευκρίνιση για κάτι που έχει ήδη αναφερθεί, αναφέρεις την υπάρχουσα πληροφορία και ζητάς συγκεκριμένη διευκρίνιση.",
            "ΣΥΛΛΟΓΗ ΣΤΟΙΧΕΙΩΝ: Εξάγε φυσικά από τη συνομιλία: αριθμό κυκλοφορίας, όνομα, τοποθεσία, προορισμό. Αν έχουν ήδη δοθεί, χρησιμοποιήστε τα.",
            "Κατάλαβε από το πλαίσιο αν είναι AC (ατύχημα) ή RA (βλάβη) χωρίς άκαμπτους κανόνες",
            "Αναγνώρισε fast track περιπτώσεις (προφανή ατυχήματα όπως χτύπημα από πίσω, παρκαρισμένο όχημα)",
            "Εντόπισε πιθανή απάτη (οικογένεια/φίλοι, ύποπτες περιστάσεις) με κοινή λογική",
            "Καθόρισε αν χρειάζεται γεωεντοπισμός (ασαφής τοποθεσία, εθνική οδός)",
            "Κρίνε αν χρειάζεται υπεύθυνη δήλωση (ειδικές περιστάσεις όπως χαμηλωμένο όχημα)",
            "Εντόπισε καθυστερήσεις >1 ώρα για αποζημίωση",
            "Fast track: 'εντός 24 ωρών προχωράμε την αποζημίωση'",
            "Fraud: 'θα σας συνδέσουμε με εκπρόσωπο για λεπτομερή καταγραφή'",
            "Καθυστέρηση: 'στέλνουμε κουπόνι έκπτωσης e-Mood 50€'",
            "Γεωεντοπισμός: 'στέλνουμε link: https://geolocation.hellasdirect.gr'",
            "Υπεύθυνη δήλωση: 'στέλνουμε φόρμα: https://sign.hellasdirect.gr'",
            "Εκτός νομού: 'ενεργοποιείται διαδικασία Επαναπατρισμού'",
            "ΣΥΜΠΛΗΡΩΣΗ ΠΕΔΙΩΝ: Γέμισε όλα τα σχετικά πεδία βάσει της κατανόησής σου από τη συνομιλία.",
            "ΕΞΥΠΝΗ ΣΥΜΠΕΡΙΦΟΡΑ: Αν ο πελάτης δίνει πληροφορία που έχει ήδη δοθεί διαφορετικά, ζήτα διευκρίνιση χωρίς να τον κάνεις να αισθάνεται άσχημα.",
        ],
    )


def create_image_analysis_prompt():
    """Create system prompt for image analysis agent"""
    return SystemPromptGenerator(
        background=[
            "Είσαι ένας εξειδικευμένος αναλυτής εικόνων για την Hellas Direct.",
            "Αναλύεις φωτογραφίες που σχετίζονται με ατυχήματα αυτοκινήτων και βλάβες.",
            "Μπορείς να αναγνωρίσεις ζημιές οχημάτων, πινακίδες κυκλοφορίας, έγγραφα, και σκηνές ατυχημάτων.",
            "Εστιάζεις στη συλλογή πληροφοριών που είναι χρήσιμες για ατυχήματα και βλάβες οχημάτων",
        ],
        steps=[
            "Αναγνώρισε τον τύπο κάθε εικόνας (ζημιά, πινακίδα, έγγραφο, σκηνή ατυχήματος, βλάβη)",
            "Εξάγε όλες τις σχετικές πληροφορίες (αριθμός πινακίδας, περιγραφή ζημιάς, τοποθεσία)",
            "Αξιολόγησε τη σοβαρότητα της ζημιάς αν υπάρχει",
            "Συνδύασε τις πληροφορίες με το πλαίσιο της συνομιλίας",
            "Αν ο χρήστης δεν έχει δώσει τις πληροφορίες του (όνομα, αριθμός κυκλοφορίας, τοποθεσία, προορισμός, κτλ.)",
        ],
        output_instructions=[
            "Χρησιμοποιήσε ΜΙΚΡΑ μηνύματα, χωρίς μη απαραίτητες πληροφορίες.",
            "Απάντησε στα ελληνικά με φιλικό και επαγγελματικό τόνο.",
            "Συμπληρώστε όλα τα πεδία ανάλυσης για κάθε εικόνα.",
            "Αν ο χρήστης δεν έχει δώσει τις πληροφορίες του (όνομα, αριθμός κυκλοφορίας, τοποθεσία, προορισμός, κτλ.)",
        ],
    )


def create_case_decision_agent(client):
    """Create case decision agent for AC/RA classification"""
    return BaseAgent(
        config=BaseAgentConfig(
            client=client,
            model="gpt-4.1",
            system_prompt_generator=create_case_decision_system_prompt(),
            input_schema=CaseDecisionInputSchema,
            output_schema=CaseDecisionOutputSchema,
        )
    )


def create_image_analyzer(client):
    """Create image analysis agent"""
    return BaseAgent(
        config=BaseAgentConfig(
            client=client,
            model="gpt-4.1-mini",
            system_prompt_generator=create_image_analysis_prompt(),
            input_schema=ImageAnalysisInput,
            output_schema=ImageAnalysisOutput,
        )
    )


def create_chat_agent(client, memory, session_context: str = ""):
    """Create chat agent with memory and session context"""

    # Create base system prompt
    base_prompt = create_chat_system_prompt()

    # Always get the latest session context
    if session_context:
        # Parse existing context into key-value pairs
        context_dict = {}
        for line in session_context.split("\n"):
            if ": " in line:
                key, value = line.split(": ", 1)
                context_dict[key] = value

        # Add context to background with clear structure
        context_lines = []
        if context_dict.get("Customer Name"):
            context_lines.append(f"👤 Customer: {context_dict['Customer Name']}")
        if context_dict.get("Registration Number"):
            context_lines.append(f"🚗 Vehicle: {context_dict['Registration Number']}")
        if context_dict.get("Case Type"):
            context_lines.append(f"📋 Type: {context_dict['Case Type']}")
        if context_dict.get("Location"):
            context_lines.append(f"📍 Location: {context_dict['Location']}")
        if context_dict.get("Destination"):
            context_lines.append(f"🎯 Destination: {context_dict['Destination']}")
        if context_dict.get("Description"):
            context_lines.append(f"📝 Details: {context_dict['Description']}")

        # Add structured context to background
        enhanced_background = base_prompt.background + [
            "CURRENT CASE CONTEXT:",
            *context_lines,
        ]
        enhanced_prompt = SystemPromptGenerator(
            background=enhanced_background,
            steps=base_prompt.steps,
            output_instructions=base_prompt.output_instructions,
        )
    else:
        enhanced_prompt = base_prompt

    return BaseAgent(
        config=BaseAgentConfig(
            client=client,
            model="gpt-4.1",
            system_prompt_generator=enhanced_prompt,
            memory=memory,
            temperature=0.2,
            max_tokens=300,
            output_schema=CustomOutputSchema,
        )
    )
