from behave import when, then

@when('the user uploads a "{file_type}" image')
def step_impl(context, file_type):
    """
    Uploads a profile picture as the specified user.

    :param context: The behave context.
    :param file_type: The type of image file to upload, either "large" or "small".
    """
    profile_page = context.pages.get_profile_page()
    if file_type == "large":
        file_path = context.config_data["large_image"]
        context.logger.info("Uploading large image (>5MB)")
    elif file_type == "small":
        file_path = context.config_data["small_image"]
        context.logger.info("Uploading small image (<=5MB)")
    else:
        raise ValueError(f"Unknown file_type: {file_type}")

    profile_page.upload_profile_picture(file_path)


@then('the upload should "{expected_outcome}"')
def step_impl(context, expected_outcome):
    """
    Asserts that the upload outcome matches the expected outcome.

    :param context: The behave context.
    :param expected_outcome: The expected outcome of the upload, either "fail" or "succeed".
    """
    
    profile_page = context.pages.get_profile_page()
    msg = profile_page.get_upload_message()
    context.logger.info(f"Upload message received: {msg}")

    if expected_outcome == "fail":
        assert "File is too large. Max allowed size is 5MB." in msg, f"Expected failure message, but got: '{msg}'"
    elif expected_outcome == "succeed":
        assert "Uploaded:" in msg, f"Expected success message, but got: '{msg}'"
    else:
        raise ValueError(f"Unknown expected_outcome: {expected_outcome}")

    context.logger.info(f"Upload {expected_outcome}ed")