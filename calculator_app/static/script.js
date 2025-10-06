document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('expression');
  let shift = false;

  // Functions that should auto-insert parentheses
  const autoFuncs = ["sin(", "cos(", "tan(", "asin(", "acos(", "atan(", "sqrt(", "log(", "ln("];

  window.append = function (value) {
    let start = input.selectionStart;
    let end = input.selectionEnd;
    if (typeof start !== 'number') {
      start = input.value.length;
      end = start;
    }

    const before = input.value.slice(0, start);
    const after = input.value.slice(end);

    if (autoFuncs.includes(value)) {
      // Insert func() and place cursor inside
      const funcName = value.slice(0, -1); // remove "("
      input.value = before + funcName + "()" + after;
      input.focus();
      const cursorPos = start + funcName.length + 1; // after func(
      input.setSelectionRange(cursorPos, cursorPos);
    } else {
      // Normal insertion
      input.value = before + value + after;
      input.focus();
      const cursorPos = start + value.length;
      input.setSelectionRange(cursorPos, cursorPos);
    }
  };

  window.clearExpr = function () {
    input.value = '';
    input.focus();
  };

  window.toggleShift = function () {
    shift = !shift;
    const buttons = document.getElementById('scientificButtons');
    if (!buttons) return;

    if (shift) {
      buttons.innerHTML = `
        <button type="button" onclick="append('asin(')">asin</button>
        <button type="button" onclick="append('acos(')">acos</button>
        <button type="button" onclick="append('atan(')">atan</button>
        <button type="button" onclick="append('sqrt(')">√</button>
        <button type="button" onclick="append('^')">^</button>
        <button type="button" onclick="append('ln(')">ln</button>
      `;
    } else {
      buttons.innerHTML = `
        <button type="button" onclick="append('sin(')">sin</button>
        <button type="button" onclick="append('cos(')">cos</button>
        <button type="button" onclick="append('tan(')">tan</button>
        <button type="button" onclick="append('sqrt(')">√</button>
        <button type="button" onclick="append('^')">^</button>
        <button type="button" onclick="append('log(')">log</button>
      `;
    }
    input.focus();
  };

  // Keyboard support
  input.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      document.getElementById('calcForm').submit();
    }
    // Let Backspace, numbers, operators, parentheses behave normally
    if (/^[0-9+\-*/().]$/.test(event.key)) return;
    if (event.key === 'Backspace') return;
    // Block everything else
    event.preventDefault();
  });
});
