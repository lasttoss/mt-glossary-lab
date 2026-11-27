#!/usr/bin/env bash
# verify.sh — một lệnh trả lời: repo này có "đúng" không? Exit 0 = sạch.
# Tự nhận stack. Ưu tiên target `test` của repo; WARN cho phần thiếu công cụ,
# FAIL chỉ khi có test/lint thật sự chạy và thất bại.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
FAIL=0; RAN=0
step() { printf '\n== %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
warn() { printf 'WARN  %s\n' "$*"; }

# JDK: mvnw cần JAVA_HOME
if command -v java >/dev/null 2>&1; then
  JREAL=$(readlink -f "$(command -v java)" 2>/dev/null || command -v java)
  CAND=$(dirname "$(dirname "$JREAL")")
  [ -x "$CAND/bin/javac" ] && export JAVA_HOME="${JAVA_HOME:-$CAND}"
fi

HAS_JDK=0
if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then HAS_JDK=1; fi

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

if grep -qE '^test:' Makefile 2>/dev/null && { [ ! -f pom.xml ] || [ "$HAS_JDK" = 1 ]; }; then
  step "make test (repo tự định nghĩa)"
  make test || fail "make test"; RAN=1
fi

if [ "$RAN" = "0" ]; then
  if [ -f pom.xml ] && [ -x ./mvnw ]; then
    if [ -z "${JAVA_HOME:-}" ]; then warn "không tìm thấy JDK ⇒ bỏ qua Maven test"
    else step "mvnw test"; ./mvnw -B test 2>&1 | tail -12 || fail "mvnw test"; fi
  elif [ -f go.mod ]; then
    step "go vet + go test"
    go vet ./... 2>&1 | tail -5 || fail "go vet"
    go test ./... || fail "go test"
  elif [ -f package.json ]; then
    if [ ! -d node_modules ]; then
      warn "chưa có node_modules ⇒ bỏ qua build/test (npm i trước)"
      RAN=1
    fi
    if [ "$RAN" = "0" ] && [ -f tsconfig.json ]; then
      step "tsc --noEmit"; npx --no-install tsc --noEmit 2>&1 | tail -8 || fail "tsc"
    fi
    if [ "$RAN" = "0" ] && $PY -c 'import json,sys;d=json.load(open("package.json"));sys.exit(0 if "build" in d.get("scripts",{}) else 1)'; then
      step "npm run build"; npm run build --silent 2>&1 | tail -8 || fail "npm run build"
    fi
    if [ "$RAN" = "0" ] && $PY -c 'import json,sys;d=json.load(open("package.json"));sys.exit(0 if "test" in d.get("scripts",{}) else 1)'; then
      step "npm test"; npm test --silent 2>&1 | tail -12 || fail "npm test"
    elif [ "$RAN" = "0" ]; then warn "package.json không có script test"; fi
  elif [ -f pyproject.toml ] || [ -d tests ]; then
    step "python tests ($PY)"
    if $PY -c 'import pytest' >/dev/null 2>&1; then
      $PY -m pytest -q 2>&1 | tail -12 || fail "pytest"
    elif [ -d tests ]; then
      $PY -m unittest discover -s tests -q 2>&1 | tail -12 || fail "unittest"
    else warn "không có pytest và không có thư mục tests/"; fi
  elif [ -f CMakeLists.txt ]; then
    if [ -d build ]; then step "ctest"; (cd build && ctest --output-on-failure 2>&1 | tail -10) || fail "ctest"
    else warn "CMake project nhưng chưa có build/ ⇒ bỏ qua"; fi
  else
    warn "không phát hiện test suite"
  fi
fi

PRE="$HOME/.pi/agent/scripts/preflight.sh"
if [ -f "$PRE" ]; then step "preflight (rule lint)"; bash "$PRE" --rules-only || fail "preflight"; fi

printf '\n== VERIFY: %s\n' "$([ "$FAIL" = 0 ] && echo OK || echo "FAIL ($FAIL)")"
[ "$FAIL" = 0 ] || exit 1
