CREATE DATABASE IF NOT EXISTS fixflow CHARACTER SET utf8mb4;
USE fixflow;

CREATE TABLE IF NOT EXISTS users (
  user_id       INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('student','admin','staff') NOT NULL DEFAULT 'student',
  team          VARCHAR(50) NULL,              -- for staff: Electrical, Plumbing, IT, Housekeeping, Carpentry
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issues (
  issue_id        INT AUTO_INCREMENT PRIMARY KEY,
  user_id         INT NOT NULL,                -- original reporter
  title           VARCHAR(150) NOT NULL,
  description     TEXT NOT NULL,
  ai_summary      VARCHAR(255) NULL,
  category        ENUM('Equipment','Electrical','Plumbing','Cleaning','Furniture','Internet','Doors/Windows','Other') NOT NULL,
  block           VARCHAR(50)  NOT NULL,       -- e.g. "Block A"
  building        VARCHAR(80)  NULL,           -- building / floor
  room            VARCHAR(80)  NULL,           -- e.g. "Room 204" or "Corridor near canteen"
  priority        ENUM('Low','Medium','High','Critical') NOT NULL DEFAULT 'Medium',
  status          ENUM('Open','Assigned','In Progress','Resolved') NOT NULL DEFAULT 'Open',
  image_url       VARCHAR(500) NULL,
  ai_category     VARCHAR(50) NULL,            -- what AI suggested (for transparency)
  ai_priority     VARCHAR(20) NULL,
  support_count   INT NOT NULL DEFAULT 1,      -- reporter + supporters
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  resolved_at     TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  INDEX idx_status (status),
  INDEX idx_priority (priority),
  INDEX idx_category (category),
  INDEX idx_location (block, room)
);

CREATE TABLE IF NOT EXISTS assignments (
  assignment_id INT AUTO_INCREMENT PRIMARY KEY,
  issue_id      INT NOT NULL,
  staff_id      INT NOT NULL,
  assigned_by   INT NOT NULL,
  assigned_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (issue_id) REFERENCES issues(issue_id) ON DELETE CASCADE,
  FOREIGN KEY (staff_id) REFERENCES users(user_id),
  FOREIGN KEY (assigned_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS comments (
  comment_id INT AUTO_INCREMENT PRIMARY KEY,
  issue_id   INT NOT NULL,
  user_id    INT NOT NULL,
  comment    TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (issue_id) REFERENCES issues(issue_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Students who "support" an existing issue instead of creating a duplicate
CREATE TABLE IF NOT EXISTS issue_supporters (
  issue_id   INT NOT NULL,
  user_id    INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (issue_id, user_id),
  FOREIGN KEY (issue_id) REFERENCES issues(issue_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Timeline of status changes
CREATE TABLE IF NOT EXISTS status_history (
  history_id  INT AUTO_INCREMENT PRIMARY KEY,
  issue_id    INT NOT NULL,
  old_status  VARCHAR(20) NULL,
  new_status  VARCHAR(20) NOT NULL,
  changed_by  INT NOT NULL,
  changed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (issue_id) REFERENCES issues(issue_id) ON DELETE CASCADE,
  FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

-- In-app notifications
CREATE TABLE IF NOT EXISTS notifications (
  notification_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id         INT NOT NULL,
  message         TEXT NOT NULL,
  is_read         BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_user_read (user_id, is_read)
);
