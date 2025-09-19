##  Overview
This project automates **profile picture upload validation** on a sample web page:
- Upload **fails** if the image is **larger than 5MB**
- Upload **succeeds** if the image is **≤ 5MB**

The framework is built using:
- **Python 3.11+**
- **Selenium WebDriver**
- **Behave (BDD framework)**
- **Page Object Model (POM) with PageFactory**
- **Automatic logging & screenshots on failures**

---

## Project Structure

```plaintext
qa_profile_upload_test/
├── config/                 # Config file
│   ├── config.json
│
├── features/               # Feature files & step definitions
│   ├── profile_page.feature
│   ├── steps/
│   │   ├── auth_steps.py
│   │   └── profile_steps.py
│   └── environment.py      # Behave hooks (setup/teardown, logging, reporting)
│
├── locators/               # Element locators (AuthLocators, ProfileLocators)
│
├── pages/                  # Page Objects + BasePage
│   ├── base_page.py
│   ├── auth_page.py
│   └── profile_page.py
│
├── utils/                  # Helpers (logger, page factory, config loader)
│
├── tests/test_files/       # Test files (dummy images for upload)
│   ├── small_image.jpg     # < 5MB
│   └── large_image.jpg     # > 5MB
│
├── reports/                # Auto-generated logs & screenshots (per run)
│
├── requirements.txt        # Python dependencies
└── README.md               # Project
```
---
## Setup Instructions

- Create Virtual Environment and install required libraries
```
- python -m venv venv_selenium
- venv_selenium\Scripts\activate (Windows)
- source venv_selenium/bin/activate (Linux/Mac)
- pip install -r requirements.txt
```

## Execution of Tests

- **behave features/profile_upload.feature**
