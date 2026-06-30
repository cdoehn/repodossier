from __future__ import annotations

from repodossier.bash_symbols import BashFunction
from repodossier.bash_symbols import discover_bash_functions
from repodossier.bash_symbols import extract_bash_functions


def test_discovers_common_bash_function_forms():
    script = """simple_func() {
  echo simple
}

function keyword_func {
  echo keyword
}

function keyword_paren_func() {
  echo keyword paren
}

spaced_func () {
  echo spaced
}

one_line_func() { echo one line; }
"""

    functions = discover_bash_functions(script, path="scripts/deploy.sh")

    assert [function.name for function in functions] == [
        "simple_func",
        "keyword_func",
        "keyword_paren_func",
        "spaced_func",
        "one_line_func",
    ]
    assert all(isinstance(function, BashFunction) for function in functions)
    assert {function.language for function in functions} == {"bash"}
    assert {function.symbol_type for function in functions} == {"function"}
    assert functions[0].path == "scripts/deploy.sh"
    assert functions[0].signature == "simple_func()"


def test_reports_start_and_end_lines():
    script = """first_func() {
  echo first
}

second_func() { echo second; }
"""

    functions = discover_bash_functions(script)

    assert [(function.name, function.start_line, function.end_line) for function in functions] == [
        ("first_func", 1, 3),
        ("second_func", 5, 5),
    ]


def test_discovers_function_with_nested_control_blocks():
    script = """deploy() {
  if build; then
    restart_service
  fi
}
"""

    functions = discover_bash_functions(script)

    assert [(function.name, function.start_line, function.end_line) for function in functions] == [
        ("deploy", 1, 5),
    ]


def test_ignores_comments_strings_and_reserved_words():
    script = """# fake_comment_func() {
echo "fake_string_func() {"
if something; then
  echo ok
fi

real_func() {
  echo ok
}
"""

    functions = discover_bash_functions(script)

    assert [function.name for function in functions] == ["real_func"]


def test_ignores_common_builtin_like_fake_functions():
    script = """echo() {
  echo not treated as project function
}

printf() {
  echo not treated as project function
}

actual_function() {
  echo ok
}
"""

    functions = discover_bash_functions(script)

    assert [function.name for function in functions] == ["actual_function"]


def test_extract_bash_functions_alias_matches_discovery():
    script = """build_assets() {
  echo build
}
"""

    assert extract_bash_functions(script) == discover_bash_functions(script)


def test_ignores_function_like_text_inside_heredocs():
    script = """real_func() {
  cat <<EOF
fake_func() {
  echo fake
}
EOF
  echo done
}

after_func() {
  echo after
}
"""

    functions = discover_bash_functions(script)

    assert [function.name for function in functions] == ["real_func", "after_func"]


def test_tolerates_subshells_and_grouping_inside_functions():
    script = """grouped_func() {
  (
    echo in subshell
  )
  {
    echo in group
  }
}

after_grouped_func() {
  echo after
}
"""

    functions = discover_bash_functions(script)

    assert [(function.name, function.start_line, function.end_line) for function in functions] == [
        ("grouped_func", 1, 8),
        ("after_grouped_func", 10, 12),
    ]


def test_rejects_invalid_bash_function_names():
    script = """123_invalid() {
  echo nope
}

valid_function() {
  echo ok
}
"""

    functions = discover_bash_functions(script)

    assert [function.name for function in functions] == ["valid_function"]
