(function () {
  'use strict';

  console.log('也不可以在控制台攻击我的博客！');

  /* 用户表：口令存的是散列，源码里没有明文 */
  var U = [
    { id: 1, n: 'autleave', p: 2277708044 },
    { id: 2, n: 'guest', p: 260620621 }
  ];

  /* 解密密钥：逐字节异或过的码点 */
  var _k = [34, 51, 41, 50, 51, 119, 104, 106, 104, 108, 119, 41, 43, 54, 119, 51, 52, 48, 63, 57, 46, 51, 53, 52];
  var K = new Uint8Array(_k.length);
  for (var i = 0; i < _k.length; i++) K[i] = _k[i] ^ 0x5a;

  var COL = { name: 'n', pass: 'p' };

  function H(s) {
    var x = 5381;
    for (var i = 0; i < s.length; i++) x = (((x << 5) + x) + s.charCodeAt(i)) >>> 0;
    return x;
  }

  /* ---------- 玩具 SQL 引擎 ---------- */
  function atom(e) {
    var m = e.match(/^(\d+)\s*=\s*(\d+)$/);
    if (m) return m[1] === m[2];

    m = e.match(/^'(.*)'\s*=\s*'(.*)'$/);
    if (m) return m[1] === m[2];

    m = e.match(/^([A-Za-z_]\w*)\s*=\s*'(.*)'$/);
    if (!m) return false;

    var c = COL[m[1].toLowerCase()] || m[1].toLowerCase();
    var v = m[2];

    if (c === 'p') {
      var hv = H(v);
      return U.some(function (u) { return u.p === hv; });
    }
    return U.some(function (u) {
      var val = u[c];
      return String(val === undefined ? '' : val) === v;
    });
  }

  function cond(e) {
    var parts = e.split(/\s+AND\s+/i);
    for (var i = 0; i < parts.length; i++) {
      if (!atom(parts[i].trim())) return false;
    }
    return true;
  }

  function run(user, pass) {
    var sql = "SELECT * FROM users WHERE name = '" + user + "' AND pass = '" + pass + "'";
    var cut = sql.indexOf('--');
    var s = cut >= 0 ? sql.slice(0, cut) : sql;
    var at = s.indexOf('WHERE ');
    if (at < 0) return false;

    var cs = s.slice(at + 6).split(/\s+OR\s+/i);
    for (var i = 0; i < cs.length; i++) {
      if (cond(cs[i].trim())) return true;
    }
    return false;
  }

  /* ---------- 解密 ---------- */
  function keystream(n) {
    var out = new Uint8Array(n), off = 0, c = 0;
    function step() {
      if (off >= n) return Promise.resolve(out);
      var buf = new Uint8Array(K.length + 4);
      buf.set(K, 0);
      new DataView(buf.buffer).setUint32(K.length, c, false);
      return crypto.subtle.digest('SHA-256', buf).then(function (d) {
        var hb = new Uint8Array(d);
        out.set(hb.subarray(0, Math.min(32, n - off)), off);
        off += 32; c++;
        return step();
      });
    }
    return step();
  }

  function dec(b64) {
    var raw = Uint8Array.from(atob(b64), function (ch) { return ch.charCodeAt(0); });
    return keystream(raw.length).then(function (ks) {
      var out = new Uint8Array(raw.length);
      for (var i = 0; i < raw.length; i++) out[i] = raw[i] ^ ks[i];
      return new TextDecoder().decode(out);
    });
  }

  /* ---------- 界面 ---------- */
  var form = document.getElementById('xishi-login');
  var msg = document.getElementById('x-msg');
  var body = document.getElementById('x-body');
  if (!form || !msg || !body) return;

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();

    var u = document.getElementById('x-u').value;
    var p = document.getElementById('x-p').value;

    if (!run(u, p)) {
      msg.textContent = '登录失败，请检查账号密码。';
      msg.className = 'login-msg error';
      return;
    }

    msg.textContent = '登录成功，正在加载…';
    msg.className = 'login-msg ok';

    fetch('/xishi/secret.json', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (j) { return dec(j.c); })
      .then(function (html) {
        body.innerHTML = html;
        body.hidden = false;
        form.hidden = true;
        body.scrollIntoView({ behavior: 'smooth', block: 'start' });
      })
      .catch(function () {
        msg.textContent = '加载失败，请稍后重试。';
        msg.className = 'login-msg error';
      });
  });
})();
