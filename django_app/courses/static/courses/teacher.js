(function () {
  'use strict';
  var language='zh',busy=false,refreshing=false,refreshQueued=false,generation=0;
  try{if(localStorage.getItem('cs-lang')==='en')language='en'}catch(error){}
  function text(key){return window.REQUEST_STRINGS[language][key]||window.REQUEST_STRINGS.zh[key]}
  function translate(){
    document.querySelectorAll('[data-review-i18n]').forEach(function(element){element.textContent=text(element.dataset.reviewI18n)});
    document.querySelectorAll('[data-review-time]').forEach(function(element){element.textContent=new Date(element.dateTime).toLocaleString(language==='en'?'en-US':'zh-TW',{timeZone:'Asia/Taipei'})});
    document.getElementById('requestLang').value=language;
  }
  function csrf(){var match=document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);return match?decodeURIComponent(match[1]):window.TEACHER_CSRF}
  async function refresh(manual){
    if(refreshing){if(manual)refreshQueued=true;return}
    if(busy||(!manual&&(document.hidden||document.activeElement.matches('[data-review-note]'))))return;
    refreshing=true;
    var serial=generation;
    try{
      var response=await fetch(location.href,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(10000)});
      if(response.redirected){location.href='/';return}if(!response.ok)throw new Error('refresh');
      var html=await response.text(),fresh=new DOMParser().parseFromString(html,'text/html').querySelector('.wrap.tch');
      if(fresh&&!busy&&serial===generation){
        if(!manual&&document.activeElement.matches('[data-review-note]'))return;
        var drafts={};
        document.querySelectorAll('[data-review-note]').forEach(function(input){drafts[input.dataset.reviewNote]=input.value});
        document.querySelector('.wrap.tch').innerHTML=fresh.innerHTML;
        document.querySelectorAll('[data-review-note]').forEach(function(input){input.value=drafts[input.dataset.reviewNote]||''});
        translate();
      }
    }catch(error){if(manual){var message=document.getElementById('reviewMessage');message.textContent=text('rSyncFailed');message.hidden=false}}
    finally{refreshing=false;if(refreshQueued){refreshQueued=false;refresh(true)}}
  }
  async function review(button){
    if(busy)return;
    var card=button.closest('[data-request-id]'),id=card.dataset.requestId;
    var note=document.getElementById('review-note-'+id).value;
    busy=true;generation++;
    document.querySelectorAll('[data-decision]').forEach(function(item){item.disabled=true});
    button.textContent=text('rReviewBusy');document.getElementById('reviewMessage').hidden=true;
    try{
      var response=await fetch('/api/applications/'+encodeURIComponent(id)+'/review/',{
        method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},
        body:JSON.stringify({decision:button.dataset.decision,note:note}),signal:AbortSignal.timeout(30000)
      });
      if(response.status===401){location.href='/';return}
      var data=await response.json();
      if(!response.ok)throw {code:data.error};
      busy=false;generation++;await refresh(true);
    }catch(error){
      var keys={course_conflict:'rConflict',no_seats:'rFull',already_reviewed:'rReviewed',not_course_teacher:'rForbidden',selection_limit:'rLimit'};
      var message=document.getElementById('reviewMessage');message.textContent=text(keys[error.code]||'rReviewFailed');message.hidden=false;
    }finally{
      busy=false;document.querySelectorAll('[data-decision]').forEach(function(item){item.disabled=false});translate();
    }
  }
  document.addEventListener('click',function(event){
    var decision=event.target.closest('[data-decision]');if(decision){review(decision);return}
    if(event.target.closest('#reviewRefresh')){refresh(true);return}
    if(event.target.closest('#logout')){
      fetch('/auth/logout/',{method:'POST',headers:{'X-CSRFToken':csrf()},credentials:'same-origin'})
        .catch(function(){}).then(function(){location.href='/'});
    }
  });
  document.addEventListener('change',function(event){
    if(event.target.id==='requestLang'){
      language=event.target.value;try{localStorage.setItem('cs-lang',language)}catch(error){}translate();
    }
  });
  setInterval(function(){refresh(false)},15000);
  translate();
}());
