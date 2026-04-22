/* ============================================================
   AUTH.JS – Dùng chung cho login.html và register.html
   ============================================================ */

/* ── Tab switching ── */
function switchTab(btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
}

/* ── Toggle password visibility ── */
function togglePwd(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon  = btn.querySelector('i');
    if (input.type === 'password') {
        input.type    = 'text';
        icon.className = 'fa fa-eye-slash';
    } else {
        input.type    = 'password';
        icon.className = 'fa fa-eye';
    }
}

/* ── Show rules box on focus ── */
function showRules(rulesId) {
    const el = document.getElementById(rulesId);
    if (el) el.style.display = 'flex';
}

/* ── Password strength checker ── */
function checkStrength(input, barId, lblId, rulesId) {
    const val    = input.value;
    const prefix = rulesId.replace('rules', 'r');  // r1, r2, r3 …

    const checks = {
        len: val.length >= 8,
        upp: /[A-Z]/.test(val),
        low: /[a-z]/.test(val),
        num: /\d/.test(val),
        spc: /[!@#$%^&*()\-_=+\[\]{};\':"\\|,.<>\/?`~]/.test(val),
    };

    // Update checklist icons
    Object.entries(checks).forEach(([k, ok]) => {
        const li = document.getElementById(`${prefix}-${k}`);
        if (!li) return;
        li.className = ok ? 'ok' : '';
        const icon = li.querySelector('i');
        if (icon) {
            icon.className = ok ? 'fa fa-circle-check' : 'fa fa-circle';
        }
    });

    const score = Object.values(checks).filter(Boolean).length;

    // Update strength bars
    const bars   = document.querySelectorAll(`#${barId} .bar`);
    const levels = ['', 's1', 's2', 's3', 's4'];
    const labels = ['', 'Yếu', 'Trung bình', 'Khá', 'Mạnh'];
    const labelColors = {
        s1: '#cc0000',
        s2: '#cc6600',
        s3: '#cc9900',
        s4: '#005a1e',
    };

    bars.forEach((b, i) => {
        b.className = 'bar';
        if (i < score) b.classList.add(levels[score]);
    });

    const lbl = document.getElementById(lblId);
    if (lbl) {
        if (!val.length) {
            lbl.textContent = '';
        } else {
            lbl.textContent  = labels[score] || '';
            lbl.style.color  = labelColors[levels[score]] || '#6b7a9a';
        }
    }

    const rulesEl = document.getElementById(rulesId);
    if (rulesEl) rulesEl.style.display = val.length ? 'flex' : 'none';
}

/* ── Confirm password match ── */
function checkConfirm(pwdId, cpwdId, msgId) {
    const pwd  = document.getElementById(pwdId).value;
    const cpwd = document.getElementById(cpwdId).value;
    const msg  = document.getElementById(msgId);
    if (!msg) return;
    if (!cpwd) { msg.textContent = ''; return; }
    if (pwd === cpwd) {
        msg.textContent = '✓ Mật khẩu khớp';
        msg.style.color = '#005a1e';
    } else {
        msg.textContent = '✗ Mật khẩu chưa khớp';
        msg.style.color = '#cc0000';
    }
}

/* ── Auto-dismiss flash messages after 4s ── */
document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash-list li');
    flashes.forEach(li => {
        setTimeout(() => {
            li.style.transition = 'opacity 0.5s';
            li.style.opacity    = '0';
            setTimeout(() => li.remove(), 500);
        }, 4000);
    });
});