/* ========== 登录/注册页面公共脚本 ========== */

/* --- CSRF Token 获取 --- */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/* --- 消息提示（替代 alert） --- */
function showInlineMsg(type, message) {
  var errEl = document.getElementById('error-msg');
  if (!errEl) return;
  errEl.textContent = message;
  errEl.className = (type === 'success') ? 'success-msg' : 'error-msg';
  errEl.style.display = 'block';
  if (type === 'success') {
    setTimeout(function() { errEl.style.display = 'none'; }, 3000);
  }
}

function hideInlineMsg() {
  var errEl = document.getElementById('error-msg');
  if (errEl) { errEl.style.display = 'none'; errEl.className = 'error-msg'; }
}

/* ========== 角色动画系统 ========== */
var AuthCharacters = (function() {
  /* 内部状态 */
  var mouseX = 0, mouseY = 0;
  var isTyping = false;
  var isLookingAtEachOther = false;
  var isPurpleBlinking = false;
  var isBlackBlinking = false;
  var isPurplePeeking = false;
  var isLoginError = false;
  var isPasswordFocused = false;
  var showPassword = false;
  var typingTimer = null;
  var errorRecoverTimer = null;
  var peekTimer = null;
  var blinkPurpleTimer = null;
  var blinkBlackTimer = null;

  var passwordInput = null;
  var formFields = [];

  var shakeIds = ['purple-eyes','black-eyes','orange-eyes','yellow-eyes','yellow-mouth','orange-mouth'];

  /* 根据鼠标位置计算角色的面部偏移和身体倾斜 */
  function calcPosition(el) {
    var rect = el.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 3;
    var dx = mouseX - cx;
    var dy = mouseY - cy;
    var faceX = Math.max(-15, Math.min(15, dx / 20));
    var faceY = Math.max(-10, Math.min(10, dy / 30));
    var bodySkew = Math.max(-6, Math.min(6, -dx / 120));
    return { faceX: faceX, faceY: faceY, bodySkew: bodySkew };
  }

  /* 计算瞳孔跟随鼠标的偏移 */
  function calcPupilOffset(el, maxDist) {
    var rect = el.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;
    var dx = mouseX - cx;
    var dy = mouseY - cy;
    var dist = Math.min(Math.sqrt(dx * dx + dy * dy), maxDist);
    var angle = Math.atan2(dy, dx);
    return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist };
  }

  /* 核心：更新所有角色姿态 */
  function updateCharacters() {
    var purple = document.getElementById('char-purple');
    var black = document.getElementById('char-black');
    var orange = document.getElementById('char-orange');
    var yellow = document.getElementById('char-yellow');
    if (!purple || !black || !orange || !yellow) return;

    var purplePos = calcPosition(purple);
    var blackPos = calcPosition(black);
    var orangePos = calcPosition(orange);
    var yellowPos = calcPosition(yellow);

    var pwdLen = passwordInput ? passwordInput.value.length : 0;
    var isShowingPwd = pwdLen > 0 && showPassword;
    var isLookingAway = isPasswordFocused && !showPassword;

    /* ---- 草莓蛋糕（紫色） ---- */
    if (isShowingPwd) {
      purple.style.transform = 'skewX(0deg)';
      purple.style.height = '370px';
    } else if (isLookingAway) {
      purple.style.transform = 'skewX(-14deg) translateX(-20px)';
      purple.style.height = '410px';
    } else if (isTyping) {
      purple.style.transform = 'skewX(' + ((purplePos.bodySkew || 0) - 12) + 'deg) translateX(40px)';
      purple.style.height = '410px';
    } else {
      purple.style.transform = 'skewX(' + purplePos.bodySkew + 'deg)';
      purple.style.height = '370px';
    }

    var purpleEyes = document.getElementById('purple-eyes');
    var purpleEyeL = document.getElementById('purple-eye-l');
    var purpleEyeR = document.getElementById('purple-eye-r');
    var purplePupilL = document.getElementById('purple-pupil-l');
    var purplePupilR = document.getElementById('purple-pupil-r');

    purpleEyeL.style.height = isPurpleBlinking ? '2px' : '18px';
    purpleEyeR.style.height = isPurpleBlinking ? '2px' : '18px';

    if (isLoginError) {
      purpleEyes.style.left = '30px'; purpleEyes.style.top = '55px';
      purplePupilL.style.transform = 'translate(-3px, 4px)';
      purplePupilR.style.transform = 'translate(-3px, 4px)';
    } else if (isLookingAway) {
      purpleEyes.style.left = '20px'; purpleEyes.style.top = '25px';
      purplePupilL.style.transform = 'translate(-5px, -5px)';
      purplePupilR.style.transform = 'translate(-5px, -5px)';
    } else if (isShowingPwd) {
      purpleEyes.style.left = '20px'; purpleEyes.style.top = '35px';
      var px = isPurplePeeking ? 4 : -4;
      var py = isPurplePeeking ? 5 : -4;
      purplePupilL.style.transform = 'translate(' + px + 'px, ' + py + 'px)';
      purplePupilR.style.transform = 'translate(' + px + 'px, ' + py + 'px)';
    } else if (isLookingAtEachOther) {
      purpleEyes.style.left = '55px'; purpleEyes.style.top = '65px';
      purplePupilL.style.transform = 'translate(3px, 4px)';
      purplePupilR.style.transform = 'translate(3px, 4px)';
    } else {
      purpleEyes.style.left = (45 + purplePos.faceX) + 'px';
      purpleEyes.style.top = (40 + purplePos.faceY) + 'px';
      var po = calcPupilOffset(purpleEyeL, 5);
      purplePupilL.style.transform = 'translate(' + po.x + 'px, ' + po.y + 'px)';
      purplePupilR.style.transform = 'translate(' + po.x + 'px, ' + po.y + 'px)';
    }

    /* ---- 巧克力块（黑色） ---- */
    if (isShowingPwd) {
      black.style.transform = 'skewX(0deg)';
    } else if (isLookingAway) {
      black.style.transform = 'skewX(12deg) translateX(-10px)';
    } else if (isLookingAtEachOther) {
      black.style.transform = 'skewX(' + ((blackPos.bodySkew || 0) * 1.5 + 10) + 'deg) translateX(20px)';
    } else if (isTyping) {
      black.style.transform = 'skewX(' + ((blackPos.bodySkew || 0) * 1.5) + 'deg)';
    } else {
      black.style.transform = 'skewX(' + blackPos.bodySkew + 'deg)';
    }

    var blackEyes = document.getElementById('black-eyes');
    var blackEyeL = document.getElementById('black-eye-l');
    var blackEyeR = document.getElementById('black-eye-r');
    var blackPupilL = document.getElementById('black-pupil-l');
    var blackPupilR = document.getElementById('black-pupil-r');

    blackEyeL.style.height = isBlackBlinking ? '2px' : '16px';
    blackEyeR.style.height = isBlackBlinking ? '2px' : '16px';

    if (isLoginError) {
      blackEyes.style.left = '15px'; blackEyes.style.top = '40px';
      blackPupilL.style.transform = 'translate(-3px, 4px)';
      blackPupilR.style.transform = 'translate(-3px, 4px)';
    } else if (isLookingAway) {
      blackEyes.style.left = '10px'; blackEyes.style.top = '20px';
      blackPupilL.style.transform = 'translate(-4px, -5px)';
      blackPupilR.style.transform = 'translate(-4px, -5px)';
    } else if (isShowingPwd) {
      blackEyes.style.left = '10px'; blackEyes.style.top = '28px';
      blackPupilL.style.transform = 'translate(-4px, -4px)';
      blackPupilR.style.transform = 'translate(-4px, -4px)';
    } else if (isLookingAtEachOther) {
      blackEyes.style.left = '32px'; blackEyes.style.top = '12px';
      blackPupilL.style.transform = 'translate(0px, -4px)';
      blackPupilR.style.transform = 'translate(0px, -4px)';
    } else {
      blackEyes.style.left = (26 + blackPos.faceX) + 'px';
      blackEyes.style.top = (32 + blackPos.faceY) + 'px';
      var bo = calcPupilOffset(blackEyeL, 4);
      blackPupilL.style.transform = 'translate(' + bo.x + 'px, ' + bo.y + 'px)';
      blackPupilR.style.transform = 'translate(' + bo.x + 'px, ' + bo.y + 'px)';
    }

    /* ---- 橘子瓣（橙色） ---- */
    var orangeMouth = document.getElementById('orange-mouth');
    if (isLoginError) {
      orangeMouth.style.left = (80 + orangePos.faceX) + 'px';
      orangeMouth.style.top = '130px';
    }
    if (isShowingPwd) {
      orange.style.transform = 'skewX(0deg)';
    } else {
      orange.style.transform = 'skewX(' + orangePos.bodySkew + 'deg)';
    }

    var orangeEyes = document.getElementById('orange-eyes');
    var orangePupilL = document.getElementById('orange-pupil-l');
    var orangePupilR = document.getElementById('orange-pupil-r');

    if (isLoginError) {
      orangeEyes.style.left = '60px'; orangeEyes.style.top = '95px';
      orangePupilL.style.transform = 'translate(-3px, 4px)';
      orangePupilR.style.transform = 'translate(-3px, 4px)';
    } else if (isLookingAway) {
      orangeEyes.style.left = '50px'; orangeEyes.style.top = '75px';
      orangePupilL.style.transform = 'translate(-5px, -5px)';
      orangePupilR.style.transform = 'translate(-5px, -5px)';
    } else if (isShowingPwd) {
      orangeEyes.style.left = '50px'; orangeEyes.style.top = '85px';
      orangePupilL.style.transform = 'translate(-5px, -4px)';
      orangePupilR.style.transform = 'translate(-5px, -4px)';
    } else {
      orangeEyes.style.left = (82 + orangePos.faceX) + 'px';
      orangeEyes.style.top = (90 + orangePos.faceY) + 'px';
      var oo = calcPupilOffset(orangePupilL, 5);
      orangePupilL.style.transform = 'translate(' + oo.x + 'px, ' + oo.y + 'px)';
      orangePupilR.style.transform = 'translate(' + oo.x + 'px, ' + oo.y + 'px)';
    }

    /* ---- 芝士块（黄色） ---- */
    if (isShowingPwd) {
      yellow.style.transform = 'skewX(0deg)';
    } else {
      yellow.style.transform = 'skewX(' + yellowPos.bodySkew + 'deg)';
    }

    var yellowEyes = document.getElementById('yellow-eyes');
    var yellowPupilL = document.getElementById('yellow-pupil-l');
    var yellowPupilR = document.getElementById('yellow-pupil-r');
    var yellowMouth = document.getElementById('yellow-mouth');

    if (isLoginError) {
      yellowEyes.style.left = '35px'; yellowEyes.style.top = '45px';
      yellowPupilL.style.transform = 'translate(-3px, 4px)';
      yellowPupilR.style.transform = 'translate(-3px, 4px)';
      yellowMouth.style.left = '30px'; yellowMouth.style.top = '92px';
      yellowMouth.style.transform = 'rotate(-8deg)';
    } else if (isLookingAway) {
      yellowEyes.style.left = '20px'; yellowEyes.style.top = '30px';
      yellowPupilL.style.transform = 'translate(-5px, -5px)';
      yellowPupilR.style.transform = 'translate(-5px, -5px)';
      yellowMouth.style.left = '15px'; yellowMouth.style.top = '78px';
      yellowMouth.style.transform = 'rotate(0deg)';
    } else if (isShowingPwd) {
      yellowEyes.style.left = '20px'; yellowEyes.style.top = '35px';
      yellowPupilL.style.transform = 'translate(-5px, -4px)';
      yellowPupilR.style.transform = 'translate(-5px, -4px)';
      yellowMouth.style.left = '10px'; yellowMouth.style.top = '88px';
      yellowMouth.style.transform = 'rotate(0deg)';
    } else {
      yellowEyes.style.left = (52 + yellowPos.faceX) + 'px';
      yellowEyes.style.top = (40 + yellowPos.faceY) + 'px';
      var yo = calcPupilOffset(yellowPupilL, 5);
      yellowPupilL.style.transform = 'translate(' + yo.x + 'px, ' + yo.y + 'px)';
      yellowPupilR.style.transform = 'translate(' + yo.x + 'px, ' + yo.y + 'px)';
      yellowMouth.style.left = (40 + yellowPos.faceX) + 'px';
      yellowMouth.style.top = (88 + yellowPos.faceY) + 'px';
      yellowMouth.style.transform = 'rotate(0deg)';
    }
  }

  /* 错误动画：角色低头摇晃 */
  function triggerLoginError() {
    if (errorRecoverTimer) { clearTimeout(errorRecoverTimer); errorRecoverTimer = null; }

    var shakeEls = shakeIds.map(function(id) { return document.getElementById(id); }).filter(Boolean);
    shakeEls.forEach(function(el) { el.classList.remove('shake-head'); });
    void document.body.offsetHeight;

    isLoginError = true;
    isPasswordFocused = false;
    updateCharacters();

    var orangeMouth = document.getElementById('orange-mouth');
    if (orangeMouth) orangeMouth.classList.add('visible');

    setTimeout(function() {
      shakeEls.forEach(function(el) { el.classList.add('shake-head'); });
    }, 350);

    errorRecoverTimer = setTimeout(function() {
      isLoginError = false;
      errorRecoverTimer = null;
      if (orangeMouth) orangeMouth.classList.remove('visible');
      shakeEls.forEach(function(el) { el.classList.remove('shake-head'); });
      updateCharacters();
    }, 2500);
  }

  /* 输入检测 */
  function setTyping(typing) {
    isTyping = typing;
    if (typing) {
      isLookingAtEachOther = true;
      clearTimeout(typingTimer);
      typingTimer = setTimeout(function() { isLookingAtEachOther = false; updateCharacters(); }, 800);
    } else {
      isLookingAtEachOther = false;
    }
    updateCharacters();
  }

  /* 眨眼定时器 */
  function scheduleBlinkPurple() {
    clearTimeout(blinkPurpleTimer);
    blinkPurpleTimer = setTimeout(function() {
      isPurpleBlinking = true; updateCharacters();
      setTimeout(function() {
        isPurpleBlinking = false; updateCharacters();
        scheduleBlinkPurple();
      }, 150);
    }, Math.random() * 4000 + 3000);
  }

  function scheduleBlinkBlack() {
    clearTimeout(blinkBlackTimer);
    blinkBlackTimer = setTimeout(function() {
      isBlackBlinking = true; updateCharacters();
      setTimeout(function() {
        isBlackBlinking = false; updateCharacters();
        scheduleBlinkBlack();
      }, 150);
    }, Math.random() * 4000 + 3000);
  }

  /* 偷看定时器（密码可见时） */
  function schedulePeek() {
    clearTimeout(peekTimer);
    if (passwordInput && passwordInput.value.length > 0 && showPassword) {
      peekTimer = setTimeout(function() {
        if (passwordInput && passwordInput.value.length > 0 && showPassword) {
          isPurplePeeking = true; updateCharacters();
          setTimeout(function() {
            isPurplePeeking = false; updateCharacters();
            schedulePeek();
          }, 800);
        }
      }, Math.random() * 3000 + 2000);
    }
  }

  /* --- 公开 API --- */
  return {
    /* 初始化：绑定事件 */
    init: function(config) {
      config = config || {};
      passwordInput = config.passwordInput || document.getElementById('password');
      formFields = config.formFields || [];

      /* 鼠标追踪 */
      document.addEventListener('mousemove', function(e) {
        mouseX = e.clientX;
        mouseY = e.clientY;
        if (!isTyping && !isLoginError) updateCharacters();
      });

      /* 密码可见性切换 */
      if (config.toggleBtn && config.eyeIcon && config.eyeOffIcon) {
        config.toggleBtn.addEventListener('click', function() {
          showPassword = !showPassword;
          passwordInput.type = showPassword ? 'text' : 'password';
          config.eyeIcon.style.display = showPassword ? 'none' : 'block';
          config.eyeOffIcon.style.display = showPassword ? 'block' : 'none';
          updateCharacters();
          if (showPassword) schedulePeek();
        });
      }

      /* 输入框事件绑定 */
      formFields.forEach(function(field) {
        if (!field.el) return;
        field.el.addEventListener('focus', function() {
          if (field.isPassword) { isPasswordFocused = true; }
          else { setTyping(true); }
          updateCharacters();
        });
        field.el.addEventListener('blur', function() {
          if (field.isPassword) { isPasswordFocused = false; }
          else { setTyping(false); }
          updateCharacters();
        });
        field.el.addEventListener('input', function() { updateCharacters(); });
      });

      /* 启动眨眼 */
      scheduleBlinkPurple();
      scheduleBlinkBlack();

      /* 初始渲染 */
      updateCharacters();
    },

    update: updateCharacters,
    triggerError: triggerLoginError,
    getCookie: getCookie,
    showMsg: showInlineMsg,
    hideMsg: hideInlineMsg
  };
})();
