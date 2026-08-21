#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # AzulQuiz has one runtime settings module for both local and Render.
    # Assign it explicitly so a stale terminal environment cannot select the
    # removed SQLite-only test settings.
    os.environ["DJANGO_SETTINGS_MODULE"] = "quizplatform.settings"
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
