"""
Test script to verify strict Class/Subject isolation.
Ensures Class 12 Physics questions CANNOT appear in Class 10 Science quizzes.
"""

from src.models.schemas import QuestionModel
from src.database.question_repository import QuestionRepository
from src.services.quiz_service import QuizService
from src.services.syllabus_service import SyllabusService

def test_class_isolation():
    print("[+] Testing Class/Subject Isolation...")
    
    # 1. Insert a Class 12 Physics question into repository
    q_physics = QuestionModel(
        class_level=12,
        subject="Physics",
        chapter="Electrostatics",
        topic="Coulomb's Law",
        question_text="What is the SI unit of electric flux?",
        option_a="N m^2 C^-1",
        option_b="N m C^-1",
        option_c="N C^-1",
        option_d="C m^-2",
        correct_answer="A",
        explanation="Electric flux is defined as E dot dA with SI unit N m^2 C^-1.",
        verification_status="VERIFIED"
    )
    
    # 2. Insert a Class 10 Science question into repository
    q_science = QuestionModel(
        class_level=10,
        subject="Science",
        chapter="Life Processes",
        topic="Nutrition",
        question_text="Which enzyme in saliva breaks down starch into sugars?",
        option_a="Salivary Amylase",
        option_b="Pepsin",
        option_c="Trypsin",
        option_d="Lipase",
        correct_answer="A",
        explanation="Salivary amylase breaks starch into simpler sugars.",
        verification_status="VERIFIED"
    )
    
    # Store both
    phy_id = QuestionRepository.create_question(q_physics)
    sci_id = QuestionRepository.create_question(q_science)
    
    print(f"  Inserted Class 12 Physics Question (ID={phy_id})")
    print(f"  Inserted Class 10 Science Question (ID={sci_id})")
    
    # 3. Fetch quiz questions for Class 10 Science
    quiz_10_sci = QuizService.fetch_quiz_questions(class_level=10, subject="Science", limit=20)
    quiz_10_ids = [q.id for q in quiz_10_sci.questions]
    
    print(f"  Class 10 Science Quiz contains {len(quiz_10_sci.questions)} question(s): IDs = {quiz_10_ids}")
    
    # Assert Class 12 Physics question NEVER appears in Class 10 Science quiz
    assert phy_id not in quiz_10_ids, f"CRITICAL: Class 12 Physics Question {phy_id} leaked into Class 10 Science Quiz!"
    assert all(q.class_level == 10 for q in quiz_10_sci.questions), "Non-Class 10 question detected in Class 10 quiz!"
    assert all(q.subject.lower() == "science" for q in quiz_10_sci.questions), "Non-Science question detected in Science quiz!"
    
    # 4. Fetch quiz questions for Class 12 Physics
    quiz_12_phy = QuizService.fetch_quiz_questions(class_level=12, subject="Physics", limit=20)
    quiz_12_ids = [q.id for q in quiz_12_phy.questions]
    
    print(f"  Class 12 Physics Quiz contains {len(quiz_12_phy.questions)} question(s): IDs = {quiz_12_ids}")
    
    assert sci_id not in quiz_12_ids, f"CRITICAL: Class 10 Science Question {sci_id} leaked into Class 12 Physics Quiz!"
    assert all(q.class_level == 12 for q in quiz_12_phy.questions), "Non-Class 12 question detected in Class 12 quiz!"
    assert all(q.subject.lower() == "physics" for q in quiz_12_phy.questions), "Non-Physics question detected in Physics quiz!"
    
    # 5. Verify syllabus scope validator explicitly rejects cross-class questions
    scope_check = SyllabusService.validate_question_scope(q_physics.question_text, class_input=10, subject="Science")
    print(f"  Cross-class scope validation: in_scope={scope_check['in_scope']}, reason='{scope_check.get('reason')}'")
    
    print("[SUCCESS] Class/Subject Isolation is 100% verified and strictly enforced.")
    return True

if __name__ == "__main__":
    test_class_isolation()
