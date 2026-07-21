"""Export the api OpenAPI document for the contracts pipeline (M0-T15).

Deterministic: sorted keys, stable indent, no host-specific noise. Does not
require a live server or a real database — settings are supplied explicitly.
"""

from __future__ import annotations

import json
import sys

from careeros_api.app import create_app
from careeros_platform.settings import Environment, Settings


def main() -> None:
    settings = Settings(
        database_url="postgresql://localhost:5432/careeros_contracts",
        supabase_url="http://127.0.0.1:54321",
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret-at-least-32-characters-long",
        environment=Environment.DEVELOPMENT,
        app_name="career-os",
    )
    app = create_app(settings)
    document = app.openapi()
    json.dump(document, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
