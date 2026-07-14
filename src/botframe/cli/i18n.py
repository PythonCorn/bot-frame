from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAME = "botframe.toml"


class BotFrameCLIError(RuntimeError):
    """Base error raised by the Bot Frame CLI."""


@dataclass(frozen=True, slots=True)
class I18nConfig:
    project_root: Path
    source: Path
    directory: Path
    domain: str
    default_locale: str

    @property
    def source_path(self) -> Path:
        return self.project_root / self.source

    @property
    def directory_path(self) -> Path:
        return self.project_root / self.directory


def initialize_i18n(
    *,
    source: str,
    directory: str,
    domain: str,
    default_locale: str,
) -> None:
    config_path = Path.cwd() / CONFIG_FILENAME
    locales_path = Path.cwd() / directory

    if config_path.exists():
        raise BotFrameCLIError(
            f"{CONFIG_FILENAME} already exists: {config_path}"
        )

    config_content = (
        "[i18n]\n"
        f'source = "{source}"\n'
        f'directory = "{directory}"\n'
        f'domain = "{domain}"\n'
        f'default_locale = "{default_locale}"\n'
    )

    config_path.write_text(
        config_content,
        encoding="utf-8",
    )
    locales_path.mkdir(parents=True, exist_ok=True)

    print(f"Created: {config_path}")
    print(f"Created: {locales_path}")
    print()
    print("Add a locale with:")
    print("    botframe i18n add ru")


def load_config() -> I18nConfig:
    project_root = Path.cwd().resolve()
    config_path = project_root / CONFIG_FILENAME

    if not config_path.exists():
        raise BotFrameCLIError(
            f"{CONFIG_FILENAME} was not found.\n"
            "\n"
            "Initialize localization first:\n"
            "\n"
            "    botframe i18n init"
        )

    with config_path.open("rb") as file:
        data = tomllib.load(file)

    raw_i18n = data.get("i18n")

    if not isinstance(raw_i18n, dict):
        raise BotFrameCLIError(
            f"Section [i18n] is missing in {CONFIG_FILENAME}."
        )

    source_value = raw_i18n.get("source", ".")
    directory_value = raw_i18n.get(
        "directory",
        "locales",
    )
    domain = raw_i18n.get("domain", "messages")
    default_locale = raw_i18n.get(
        "default_locale",
        "en",
    )

    for name, value in {
        "source": source_value,
        "directory": directory_value,
        "domain": domain,
        "default_locale": default_locale,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise BotFrameCLIError(
                f"Invalid i18n setting {name!r}: {value!r}"
            )

    source = Path(source_value)
    directory = Path(directory_value)

    if source.is_absolute():
        raise BotFrameCLIError(
            "The i18n source path must be relative "
            "to the project root."
        )

    if directory.is_absolute():
        raise BotFrameCLIError(
            "The i18n directory path must be relative "
            "to the project root."
        )

    return I18nConfig(
        project_root=project_root,
        source=source,
        directory=directory,
        domain=domain,
        default_locale=default_locale,
    )


def require_babel() -> str:
    try:
        import babel  # noqa: F401
    except ImportError as error:
        raise BotFrameCLIError(
            "Babel is required for localization commands.\n"
            "\n"
            "Install Bot Frame with i18n support:\n"
            "\n"
            '    pip install "bot-frame[i18n]"'
        ) from error

    executable = shutil.which("pybabel")

    if executable is not None:
        return executable

    scripts_directory = Path(sys.executable).parent
    executable_name = (
        "pybabel.exe"
        if os.name == "nt"
        else "pybabel"
    )
    executable_path = scripts_directory / executable_name

    if executable_path.exists():
        return str(executable_path)

    raise BotFrameCLIError(
        "Babel is installed, but the pybabel executable "
        "could not be found."
    )


def create_mapping_file(directory: Path) -> Path:
    mapping = """\
[ignore: .venv/**]
[ignore: venv/**]
[ignore: env/**]
[ignore: **/__pycache__/**]
[ignore: **/.git/**]
[ignore: build/**]
[ignore: dist/**]

[botframe: **.py]
encoding = utf-8
"""

    mapping_path = directory / "babel.cfg"
    mapping_path.write_text(mapping, encoding="utf-8")

    return mapping_path


def run_pybabel(
    *arguments: str,
    cwd: Path | None = None,
) -> None:
    executable = require_babel()

    command = [
        executable,
        *arguments,
    ]

    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
    )

    if result.returncode != 0:
        raise BotFrameCLIError(
            "Babel command failed:\n\n"
            f"    {' '.join(command)}"
        )


def get_template_path(config: I18nConfig) -> Path:
    return (
        config.directory_path
        / f"{config.domain}.pot"
    )


def extract_catalog() -> None:
    config = load_config()

    if not config.source_path.exists():
        raise BotFrameCLIError(
            f"Source directory does not exist: "
            f"{config.source_path}"
        )

    config.directory_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    template_path = get_template_path(config)

    with tempfile.TemporaryDirectory(
        prefix="botframe-i18n-"
    ) as temporary_directory:
        temporary_path = Path(temporary_directory)
        mapping_path = create_mapping_file(
            temporary_path
        )

        run_pybabel(
            "extract",
            "--mapping-file",
            str(mapping_path),
            "--output-file",
            str(
                template_path.relative_to(
                    config.project_root
                )
            ),
            "--input-dirs",
            str(config.source),
            cwd=config.project_root,
        )

    print(f"Messages extracted to: {template_path}")


def add_locale(locale: str) -> None:
    config = load_config()
    template_path = get_template_path(config)

    locale = locale.strip()

    if not locale:
        raise BotFrameCLIError(
            "Locale must not be empty."
        )

    if not template_path.exists():
        extract_catalog()

    po_path = (
        config.directory_path
        / locale
        / "LC_MESSAGES"
        / f"{config.domain}.po"
    )

    if po_path.exists():
        raise BotFrameCLIError(
            f"Locale {locale!r} already exists: "
            f"{po_path}"
        )

    run_pybabel(
        "init",
        "--input-file",
        str(
            template_path.relative_to(
                config.project_root
            )
        ),
        "--output-dir",
        str(config.directory),
        "--domain",
        config.domain,
        "--locale",
        locale,
        cwd=config.project_root,
    )

    print(f"Locale added: {locale}")
    print(f"Catalog: {po_path}")


def find_po_catalogs(
    config: I18nConfig,
) -> list[Path]:
    pattern = (
        f"*/LC_MESSAGES/{config.domain}.po"
    )

    return sorted(
        config.directory_path.glob(pattern)
    )


def update_catalogs() -> None:
    config = load_config()

    extract_catalog()

    catalogs = find_po_catalogs(config)

    if not catalogs:
        print(
            "No translation catalogs found. "
            "Add a locale first:"
        )
        print()
        print("    botframe i18n add ru")
        return

    template_path = get_template_path(config)

    run_pybabel(
        "update",
        "--input-file",
        str(
            template_path.relative_to(
                config.project_root
            )
        ),
        "--output-dir",
        str(config.directory),
        "--domain",
        config.domain,
        cwd=config.project_root,
    )

    print(
        f"Updated {len(catalogs)} "
        "translation catalog(s)."
    )


def compile_catalogs() -> None:
    config = load_config()
    catalogs = find_po_catalogs(config)

    if not catalogs:
        raise BotFrameCLIError(
            "No PO catalogs found.\n"
            "\n"
            "Add a locale first:\n"
            "\n"
            "    botframe i18n add ru"
        )

    run_pybabel(
        "compile",
        "--directory",
        str(config.directory),
        "--domain",
        config.domain,
        cwd=config.project_root,
    )

    print(
        f"Compiled {len(catalogs)} "
        "translation catalog(s)."
    )


def build_catalogs() -> None:
    update_catalogs()

    config = load_config()

    if not find_po_catalogs(config):
        return

    compile_catalogs()