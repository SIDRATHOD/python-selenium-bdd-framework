Feature: Profile Picture Upload Validation

  Scenario Outline: Validate profile picture upload by file size
    Given the user is logged in
    When the user uploads a "<file_type>" image
    Then the upload should "<expected_outcome>"

    Examples:
      | file_type | expected_outcome |
      | large     | fail             |
      | small     | succeed          |
