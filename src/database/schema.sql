-- =========================================================
-- Study Smarter: Personal Question-Bank Practice System
-- Database Schema Definition (Local & Cloud MySQL Compatible)
-- Character Set: utf8mb4, Engine: InnoDB
-- =========================================================

-- 1. Table: Users (Students / System Users)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE DEFAULT NULL,
    class_level INT NOT NULL DEFAULT 0 COMMENT '0 = unspecified, 10 or 12 for legacy NCERT data',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_class (class_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table: Question Banks (User-defined question bank collections)
CREATE TABLE IF NOT EXISTS question_banks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    source_pdf VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bank_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Table: Quizzes (Generated Interactive Practice Sets)
CREATE TABLE IF NOT EXISTS quizzes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    class_level INT NOT NULL DEFAULT 0,
    subject VARCHAR(100) NOT NULL DEFAULT 'General',
    total_questions INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_quiz_class_subject (class_level, subject)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Table: Questions (Extracted MCQs with AI Verification & Metadata)
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class INT NOT NULL DEFAULT 0 COMMENT '0 = unspecified, 10 or 12 for legacy NCERT data',
    subject VARCHAR(100) NOT NULL DEFAULT 'General',
    chapter VARCHAR(150) DEFAULT 'General',
    topic VARCHAR(150) DEFAULT 'General',
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL COMMENT 'A, B, C, or D',
    explanation TEXT DEFAULT NULL,
    difficulty VARCHAR(20) DEFAULT 'Medium' COMMENT 'Easy, Medium, Hard',
    source_pdf VARCHAR(255) DEFAULT NULL,
    answer_confidence FLOAT DEFAULT 1.0 COMMENT 'Confidence score (0.0 to 1.0)',
    verification_status VARCHAR(50) DEFAULT 'VERIFIED' COMMENT 'UNVERIFIED, VERIFIED, AI_GENERATED',
    bank_id INT DEFAULT NULL COMMENT 'FK to question_banks - NULL = Uncategorised',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_class_subject (class, subject),
    INDEX idx_topic (topic),
    INDEX idx_verification (verification_status),
    INDEX idx_bank (bank_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Table: Attempts (Student Quiz Attempt Log & Question Details)
CREATE TABLE IF NOT EXISTS attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    quiz_id INT DEFAULT NULL,
    question_id INT NOT NULL,
    selected_answer CHAR(1) NOT NULL COMMENT 'A, B, C, or D',
    correct_answer CHAR(1) NOT NULL COMMENT 'A, B, C, or D',
    is_correct BOOLEAN NOT NULL,
    time_taken INT DEFAULT 0 COMMENT 'Time spent in seconds',
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    INDEX idx_attempt_user (user_id),
    INDEX idx_attempt_quiz (quiz_id),
    INDEX idx_attempt_question (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Initial Seed Data: Default User Account (only if missing)
INSERT IGNORE INTO users (id, name, email, class_level) VALUES
(1, 'Student', 'student@studysmarter.local', 0);

-- Default Question Bank (only if missing)
INSERT IGNORE INTO question_banks (id, name, source_pdf) VALUES
(1, 'General', NULL);
