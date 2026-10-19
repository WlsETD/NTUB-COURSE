// 由 course.html 拆出的選課介面程式。課程資料與已存的選課由 Django 放進頁面（#raw-data、#boot-data）。
(function(){
  var PERIOD_TIME=["08:10","09:10","10:10","11:10","12:10","13:10","14:10","15:10","16:10"];
  var MIN=9, MAX=25;
  // 115-1 NTUB 4-year day-programme sections, captured from the public course search on 2026-10-08.
  // [id, deptCode, source, class, year(0=open to all), code, name, teacher, slots[[day,from,to]], room, credits, capacity, enrolled, type, category, icon]
  var RAW=JSON.parse(document.getElementById("raw-data").textContent);
  var BOOT=JSON.parse(document.getElementById("boot-data").textContent);
  function byIdOK(id){return COURSES.some(function(c){return c.id===id})}
  var COURSES=RAW.map(function(r){return {id:r[0],dept:r[1],src:r[2],cls:r[3],grade:r[4],code:r[5],name:r[6],teacher:r[7],slots:r[8],room:r[9],credits:r[10],cap:r[11],enr:r[12],type:r[13],cat:r[14],icon:r[15],pre:[]}});
  var ICONS={
    code:'<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    integral:'<path d="M16 4.5c-1.5-1.2-4.5-1-4.5 2.5v10c0 3.5-3 3.7-4.5 2.5"/><path d="M15 15h4"/>',
    brush:'<path d="M14 4l6 6-7 7-6-6z"/><path d="M7 11c-2.5 0-4 1.5-4 4 0 2-1 3-1 3s5 1 7-1c1-1 1.5-2.5.5-4"/>',
    speech:'<path d="M4 5h16v11H10l-5 4v-4H4z"/><path d="M9.5 13l2.5-5.5 2.5 5.5M10.4 11.2h3.2"/>',
    atom:'<circle cx="12" cy="12" r="1.4"/><ellipse cx="12" cy="12" rx="9" ry="3.6"/><ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(120 12 12)"/>',
    shuttle:'<circle cx="7" cy="17" r="3"/><path d="M9.2 14.8L16 3M9.2 14.8L21 8M9.2 14.8l9.3-9.3"/>',
    palette:'<path d="M12 3a9 9 0 100 18c1.4 0 2-.9 2-1.8 0-1.2-1-1.6-.2-2.6.7-.8 1.8-.6 3.2-.6A4 4 0 0021 12c0-5-4-9-9-9z"/><circle cx="7.5" cy="11.5" r="1"/><circle cx="10" cy="7.5" r="1"/><circle cx="15" cy="7.5" r="1"/>',
    bulb:'<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 00-3.8 10.6c.6.6.8 1.4.8 2.4h6c0-1 .2-1.8.8-2.4A6 6 0 0012 3z"/>',
    leaf:'<path d="M5 19C5 10 11 5 20 4c-.5 9-5.5 15-14 15"/><path d="M5 19l8-8"/>',
    yoga:'<circle cx="12" cy="4.5" r="2"/><path d="M12 7.5v6M4.5 10.5l7.5 3 7.5-3M6 20l6-6.5 6 6.5M5 20h14"/>',
    tree:'<circle cx="12" cy="5" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="12" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><path d="M11 6.8l-4 9.4M12 7v9M13 6.8l4 9.4"/>',
    chip:'<rect x="7" y="7" width="10" height="10" rx="1.5"/><rect x="10" y="10" width="4" height="4"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/>',
    matrix:'<path d="M7 4H4v16h3M17 4h3v16h-3"/><circle cx="9" cy="9" r="1"/><circle cx="15" cy="9" r="1"/><circle cx="9" cy="15" r="1"/><circle cx="15" cy="15" r="1"/>',
    dice:'<rect x="4" y="4" width="16" height="16" rx="3.5"/><circle cx="8.5" cy="8.5" r="1.1"/><circle cx="12" cy="12" r="1.1"/><circle cx="15.5" cy="15.5" r="1.1"/>',
    book:'<path d="M3 5.5c3-1.2 6-1 9 1V20c-3-2-6-2.2-9-1zM21 5.5c-3-1.2-6-1-9 1V20c3-2 6-2.2 9-1z"/>',
    chart:'<path d="M4 4v16h16"/><path d="M7.5 15l3.5-4 3 3 5-6.5"/>',
    branch:'<circle cx="6" cy="5.5" r="2"/><circle cx="6" cy="18.5" r="2"/><circle cx="18" cy="12" r="2"/><path d="M6 7.5v9M8 5.5c6 0 4 6.5 8 6.5"/>',
    terminal:'<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M7 9.5l3 2.5-3 2.5M12.5 15H17"/>',
    globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3.2 3.2 3.2 14.8 0 18M12 3c-3.2 3.2-3.2 14.8 0 18"/>',
    neural:'<circle cx="5" cy="6.5" r="2"/><circle cx="5" cy="17.5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/><path d="M6.7 7.6l3.6 3.3M6.7 16.4l3.6-3.3M14 12h3"/>',
    pen:'<path d="M4 20l4.2-1L19 8.2 15.8 5 5 15.8z"/><path d="M13.8 7l3.2 3.2"/>',
    lock:'<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/><path d="M12 15v2"/>',
    cloud:'<path d="M7 18.5a4.5 4.5 0 01-.6-9A6 6 0 0118 10a4.3 4.3 0 01-.5 8.5z"/>',
    flag:'<path d="M5 21V4M5 4h12l-2.5 4.5L17 13H5"/>',
    calc:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h1M12 11h1M16 11h0M8 15h1M12 15h1M8 18h1M12 18h4M16 14v4"/>',
    scale:'<path d="M12 4v16M8 20h8M5 7h14"/><path d="M5 7l-3 6a3 3 0 006 0zM19 7l-3 6a3 3 0 006 0z"/>',
    film:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 5v14M17 5v14M3 9h4M3 15h4M17 9h4M17 15h4"/>',
    ball:'<circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18M5.6 5.6c3 3 3 9.8 0 12.8M18.4 5.6c-3 3-3 9.8 0 12.8"/>',
    run:'<circle cx="14" cy="4.5" r="2"/><path d="M8 21l3-6 3 2v5M5 12l4-4 4 1 3 3 3 1M11 15l-1.5-6"/>',
    shield:'<path d="M12 3l8 3v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z"/><path d="M9 12l2 2 4-4"/>',
    people:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.4"/><path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6M15 14.5c2.8 0 5 2 5 5"/>',
    music:'<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
    mind:'<path d="M13 3a7 7 0 00-7 7c0 1.8.6 3.2 1.8 4.4.7.7 1.2 1.6 1.2 2.6V21h6v-2h2.5a1.5 1.5 0 001.5-1.5V15l1.8-.8-1.8-3.2A7 7 0 0013 3z"/><path d="M11 9.5a2 2 0 114 0c0 1.2-1 1.6-1.6 2.3"/>',
    torii:'<path d="M3 5.5c6 1 12 1 18 0M5 9.5h14M7 6.2V21M17 6.2V21M12 9.5v3.5"/>',
    wave:'<path d="M2 13c2.5-2 4.5-2 7 0s4.5 2 7 0 4-2 6 0M2 18c2.5-2 4.5-2 7 0s4.5 2 7 0 4-2 6 0"/><circle cx="15" cy="6.5" r="2"/>'
  };
  // rainbow theme: every course gets its own colour from its code; otherwise colour follows the department
  function colIdx(c){if(typeof accentKey!=="undefined"&&accentKey==="rainbow"){var h=0;for(var i=0;i<c.code.length;i++)h=(h*31+c.code.charCodeAt(i))%9973;return h%4}return DEPTCOL[c.dept]}
  function icon(c,cls){return '<svg class="'+(cls||"ico")+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+ICONS[c.icon]+'</svg>'}
  var DEPTCOL={"400":3,"401":0,"402":1,"403":2,"404":4,"405":0,"406":1,"407":2,"40A":3,"40B":4,"40C":0,"901":2,"903":4};
  var DEPTS=["401","402","403","404","405","406","407","40A","40B","40C"];
  var DEPT_ZH={"401":"會計資訊系","402":"財務金融系","403":"財政稅務系","404":"國際商務系","405":"企業管理系","406":"資訊管理系","407":"應用外語系","40A":"商業設計管理系","40B":"創意科技與產品設計系","40C":"數位多媒體設計系"};
  var DEPT_EN2={"401":"Accounting Information","402":"Finance","403":"Public Finance and Tax Administration","404":"International Business","405":"Business Administration","406":"Information Management","407":"Applied Foreign Languages","40A":"Commercial Design and Management","40B":"Creative Technology and Product Design","40C":"Digital Multimedia Design"};
  // ---------- i18n ----------
  var LANG="zh";
  try{var sl=localStorage.getItem("cs-lang");if(sl==="en"||sl==="zh")LANG=sl}catch(e){}
  var STR={
    zh:{title:"NTUB COURSE",sub:"國立臺北商業大學 · 115 學年度第 1 學期加退選 · 四技日間部",palette:"主題色",custom:"自訂顏色",gradeAria:"選擇年級",
      search:"搜尋課名、老師或課號",noClash:"只看不衝堂",week:"本週課表",ttHint:"點空堂可查看那個時段的課",slotChip:"時段：{0}",slotClearT:"清除時段篩選",cellPick:"{0}：查看這個時段的課",slotEmpty:"{0}沒有可選的課。",slotToast:"{0}有 {1} 門課可選",navList:"課程",navTable:"課表",navMe:"進度",navAria:"主要導覽",
      themeSystem:"跟隨系統",themeLight:"淺色",themeDark:"深色",themeAria:"切換配色",langBtn:"EN",langAria:"Switch to English",langToast:"已切換為中文",
      done:"已修過此課程",minGrade:"{0}以上才能選",drawing:"抽籤進行中",noSeat:"抽籤後已無空缺名額",clash:"與「{0}」衝堂",pre:"尚未修畢先修課 {0}",overMax:"加選後超過學分上限 {0}",
      cantAdd:"無法加選：{0}",addedAfter:"已加選「{0}」，名額 {1}/{2}",regOver:"已登記「{0}」，{1}/{2} 超額，截止後抽籤",regOk:"已登記「{0}」，{1}/{2}，截止後直接錄取",
      dropReq:"已取消必修「{0}」，畢業前仍需補修",dropped:"已退選「{0}」",grpSel:"已選課程",idLine:"{0} · {1}{2} · 學號 {3}",idNoData:"{0} · 學號 {1} · 目前只有四技日間部的課程資料",prog4:"四技",prog3:"二技",homeTag:"（本系）",deptViewAria:"查看其他科系的課程",viewDept:"正在查看{0}的課程，你的選課與必修不變",viewHome:"回到本系課程",ttQ:"要退選這門課嗎？",ttKeep:"保留",ttReqWarn:"這是本班必修，退選後畢業前仍需補修。",ttBlkAria:"{0}，點選可退選",lowCredit:"提醒：目前學分低於下限 {0}",
      gradTitle:"畢業學分進度",total:"合計 {0} / {1}",gap:"差 {0}",reached:"已達成",had:"已修",now:"本學期",
      crTitle:"本學期學分",crMax:"/ 上限 {0}",selCount:"已選 {0} 門",stNeed:"尚差 {0} 學分達下限",stMax:"已達學分上限",stLeft:"可再選 {0} 學分",
      phase1:"階段一 · 登記中，可超額登記，截止後抽籤",phase3:"階段三 · 加退選，剩餘名額先搶先贏",
      miniCr:"{0} 學分",miniReg:"已登記 {0} 門",miniAdm:"已錄取 {0} 門",miniPh1:"登記中",miniPh3:"加退選",
      empty:"找不到符合的課程，換個關鍵字試試。",bDrop:"退選",bDone:"已修過",bAdd:"加選",bReg:"登記",lvl:"{0}課程",seatTitle:"已選人數 / 名額",
      stOver:"超額 · 截止後抽籤",stFull:"已滿",stFullCan:"已滿 · 可登記",stSeats:"剩 {0} 位",tReg:"已登記",tAdm:"已錄取",tAuto:"自動帶入",tAutoOff:"已取消必修",tAutoS:"自動",
      gClash:"衝堂",gPrev:"預覽",mineEmpty:"還沒有選任何課程。從左側清單加選。",cr:"{0} 學分",
      autoNote:"{0}必修 {1} 門已自動帶入，不需要可自行退選",doneLine:"已修畢 {0} 門：{1}",newbie:"新生尚無已修課程。",
      lotDrawing:"抽籤中…",lotResult:"抽籤結果",lotSum:"中籤 {0} 門 · 未中籤 {1} 門",spin:"抽籤中",direct:"直接錄取",win:"中籤",lose:"未中籤",reset:"重新登記",resetHint:"已進入加退選，空缺名額先搶先贏",
      regTitle:"登記狀態",regCount:"登記 {0} 門 · 超額 {1} 門",overList:"有 {0} 門課登記人數超過名額，截止後會抽籤：{1}",noneOver:"目前登記的課都沒有超額，截止後會全部直接錄取。",runLot:"截止並抽籤",runHint:"模擬登記截止後的抽籤批次",
      lotDone:"抽籤完成，{0} 門未中籤，可在加退選補選其他課",lotAll:"抽籤完成，全部錄取",backReg:"已回到登記階段",switched:"已切換為{0}，已自動帶入 {1} 門必修",
      stOverCap:"已選 {0} 學分，超出上限的 {1} 學分不予計算",tNoCount:"不計學分",tPartial:"計入 {0}/{1}",regExcess:"已登記「{0}」，超出 {1} 學分上限的部分不予計算",miniEx:"+{0} 不計",settings:"設定",gSub:"國立臺北商業大學 · 115-1 四技日間部",gSkip:"略過動畫",gH:"登入 NTUB COURSE",gDesc:"使用學校帳號（@ntub.edu.tw）登入，不需要另外註冊。",gLogin:"以學校帳號登入",gNote:"身分以你目前登入 Claude 的帳號 email 確認",gChecking:"確認身分中…",gNotSchool:"目前登入的帳號是 {0}，不是 @ntub.edu.tw 學校信箱，無法以學生身分登入。",gNoEmail:"這個預覽頁面無法讀取帳號 email，因此無法驗證學校信箱。正式上線版本會改用 Google 學校帳號登入。",gDemo:"以示範模式進入（未驗證身分）",gWelcome:"歡迎，{0}",gWelcomeDemo:"示範模式",gLogout:"登出",gDemoChip:"示範模式（未驗證）",bqTitle:"選課基本資料",bqHint:"個人可加選資格請以學校系統為準",bqItem:"項目",bqLimit:"上限",bqSel:"已選",bq1:"學分上下限",bq2:"總學分－已選學分",bq3:"跨部互選學分數－已選學分",bq4:"興趣選修科目數－已選",bq5:"成績優異可加選科目數－已選",bq6:"轉學轉系生可加選科目數－已選",bq7:"輔系雙主修可加選科目數－已選",bq8:"申請學程可加選科目數－已選",bq9:"研究所下修可加選科目數－已選",aiClose:"關閉",fontL:"字體",fontCubic:"俐方體11號（點陣）",fontNoto:"Noto Sans TC",fontToast:"字體：{0}",aiTitle:"AI 選課建議",aiSub:"說說你想學什麼，AI 從可選的課裡幫你挑",aiDeptL:"想從哪個學系選課",aiTextL:"你的興趣或目標",aiPh:"例如：想往資料分析發展，希望學 Python 和統計，週五不想排課",aiGo:"取得建議",aiStop:"停止",aiThinking:"AI 思考中，通常需要 10 到 40 秒…",aiNeed:"請先寫下你的興趣或目標",aiAddAll:"全部加入",aiAdd:"加入",aiAdded:"已加入",aiClash:"與已選課程衝堂",aiNone:"這個學系目前沒有可選又不衝堂的課",aiErr:"這次沒拿到建議，請稍後再試",aiDenied:"AI 服務目前無法使用（伺服器尚未設定 OpenAI 金鑰或額度不足）",saveErr:"選課沒有存到伺服器，請檢查網路；下次變動時會再試一次",saved:"已自動儲存",aiBusy:"使用太頻繁了，請稍等一下再試",aiDisc:"建議由 AI 產生，請自行確認是否符合系上規定",aiOther:"外系",aiAuto:"自動判斷（依你的描述）",aiClassify:"正在判斷和你描述相關的學系…",aiPicking:"已篩選：{0}，正在挑課…",aiChip:"AI 篩選：{0}",aiClearT:"清除 AI 篩選，只看本系課程",grpAi:"AI 篩選的外系課程 · {0}",aiFiltered:"AI 判斷相關學系：{0}。課程清單已加入這些學系的課。",deptAria:"選擇學系",srcAll:"全部",srcDept:"本系",srcGe:"通識",srcPe:"體育",srcMil:"軍訓",grpCls:"本班 · {0}",grpSame:"本系其他班級",grpViewSame:"{0}",grpViewLow:"{0} · 低年級",grpLowDept:"本系低年級 · 學分與本學期合併計算",grpGe:"通識課程",grpPe:"體育",grpMil:"軍訓",autoNote2:"{0} · 本班必修 {1} 門已自動帶入，不需要可自行退選",autoNote0:"{0} · 本班這學期沒有可自動帶入的必修，請自行選課",dSwitch0:"已切換為{0}，本班這學期沒有可自動帶入的必修",undo:"復原",undone:"已復原先前的選課",clearQ:"清除搜尋",emptyQ:"「{0}」沒有符合的課程。",searchAll:"搜尋全部類別",srcNote:"開課資料取自北商全校課程查詢（115-1 四技日間部，2026/10/08 擷取）",termBreak:"本學期計入：必修 {0} · 選修 {1} · 通識 {2}",gradNeed:"畢業最低 {0} 學分",dSwitch:"已切換為{0}，本班必修 {1} 門已自動帶入",language:"語言",appearance:"外觀",grpMine:"{0}課程",grpLower:"低年級課程 · 學分與本學期合併計算",grpDone:"已修過 {0} 門",grpShow:"展開",grpHide:"收合",deadline:"登記截止：10 月 15 日 17:00，截止後由系統抽籤並公告結果",ncOn:"只顯示和目前課表不衝堂的課",ncOff:"顯示全部課程",accentToast:"主題色：{0}",themeToast:"配色：{0}",sep:"、",slot:"週{0} {1}–{2}節",slot1:"週{0} 第{1}節",day:"週{0}"},
    en:{title:"NTUB COURSE",sub:"National Taipei University of Business · Fall 2026 add/drop · 4-year day program",palette:"Theme",custom:"Custom color",gradeAria:"Select year",
      search:"Search course, instructor or code",noClash:"Hide conflicts",week:"Weekly timetable",ttHint:"Tap a free slot to see courses at that time",slotChip:"Time: {0}",slotClearT:"Clear the time filter",cellPick:"{0}: show courses at this time",slotEmpty:"No courses available at {0}.",slotToast:"{1} courses at {0}",navList:"Courses",navTable:"Timetable",navMe:"Progress",navAria:"Main navigation",
      themeSystem:"System",themeLight:"Light",themeDark:"Dark",themeAria:"Change appearance",langBtn:"中文",langAria:"切換為中文",langToast:"Switched to English",
      done:"Already completed",minGrade:"Open to {0} and above",drawing:"Lottery in progress",noSeat:"No seats left after the lottery",clash:"Conflicts with {0}",pre:"Prerequisite not met: {0}",overMax:"Would exceed the {0}-credit limit",
      cantAdd:"Can't add: {0}",addedAfter:"Added {0} ({1}/{2})",regOver:"Registered for {0}. {1}/{2} is over capacity, so a lottery runs after the deadline",regOk:"Registered for {0} ({1}/{2}). You'll be admitted after the deadline",
      dropReq:"Removed required course {0}. You still need it to graduate",dropped:"Dropped {0}",grpSel:"Selected",idLine:"{0} · {1}, {2} · ID {3}",idNoData:"{0} · ID {1} · Only 4-year day program courses are available",prog4:"4-year program",prog3:"2-year program",homeTag:" (my dept)",deptViewAria:"Browse other departments' courses",viewDept:"Browsing {0}. Your courses and required courses stay the same",viewHome:"Back to your department",ttQ:"Drop this course?",ttKeep:"Keep",ttReqWarn:"This is a required course for your class. You'll still need to take it before you graduate.",ttBlkAria:"{0}. Select to drop",lowCredit:"Heads up: you're below the {0}-credit minimum",
      gradTitle:"Graduation progress",total:"Total {0} / {1}",gap:"{0} to go",reached:"Done",had:"Completed",now:"This term",
      crTitle:"Credits this term",crMax:"/ max {0}",selCount:"{0} courses",stNeed:"{0} more credits to reach the minimum",stMax:"At the credit limit",stLeft:"{0} credits available",
      phase1:"Phase 1 · Registration open. Over-capacity courses go to a lottery",phase3:"Phase 3 · Add/drop. Remaining seats are first come, first served",
      miniCr:"{0} cr",miniReg:"{0} registered",miniAdm:"{0} admitted",miniPh1:"Registering",miniPh3:"Add/drop",
      empty:"No matching courses. Try another keyword.",bDrop:"Drop",bDone:"Completed",bAdd:"Add",bReg:"Register",lvl:"{0} course",seatTitle:"Enrolled / capacity",
      stOver:"Over · lottery after deadline",stFull:"Full",stFullCan:"Full · can register",stSeats:"{0} left",tReg:"Registered",tAdm:"Admitted",tAuto:"Auto-added",tAutoOff:"Required, removed",tAutoS:"Auto",
      gClash:"Conflict",gPrev:"Preview",mineEmpty:"No courses yet. Add some from the list.",cr:"{0} cr",
      autoNote:"{1} required {0} courses were added for you. Drop any you don't need.",doneLine:"Completed {0}: {1}",newbie:"No completed courses yet.",
      lotDrawing:"Drawing…",lotResult:"Lottery results",lotSum:"{0} won · {1} not drawn",spin:"Drawing",direct:"Admitted",win:"Won",lose:"Not drawn",reset:"Start over",resetHint:"Add/drop is open. Remaining seats are first come, first served",
      regTitle:"Registration",regCount:"{0} registered · {1} over capacity",overList:"{0} of your courses are over capacity and will go to a lottery: {1}",noneOver:"None of your courses are over capacity, so you'll be admitted to all of them.",runLot:"Close and run lottery",runHint:"Simulates the lottery after the deadline",
      lotDone:"Lottery done. {0} course(s) not drawn; pick others during add/drop",lotAll:"Lottery done. You're admitted to everything",backReg:"Back to registration",switched:"Switched to {0}. {1} required courses added",
      stOverCap:"{0} credits selected. The {1} over the limit won't count",tNoCount:"Not counted",tPartial:"{0}/{1} cr counted",regExcess:"Registered for {0}. Credits over the {1}-credit limit won't count",miniEx:"+{0} not counted",settings:"Settings",gSub:"National Taipei University of Business · Fall 2026 · 4-year day program",gSkip:"Skip intro",gH:"Sign in to NTUB COURSE",gDesc:"Sign in with your school account (@ntub.edu.tw). No separate sign-up needed.",gLogin:"Sign in with school account",gNote:"Your identity is checked against the email of the Claude account you are signed in with",gChecking:"Checking your account…",gNotSchool:"You are signed in as {0}, which is not an @ntub.edu.tw school address, so you can't sign in as a student.",gNoEmail:"This preview can't read your account email, so it can't verify a school address. The deployed version signs in with Google school accounts.",gDemo:"Enter demo mode (identity not verified)",gWelcome:"Welcome, {0}",gWelcomeDemo:"Demo mode",gLogout:"Sign out",gDemoChip:"Demo mode (not verified)",bqTitle:"Registration quotas",bqHint:"Personal eligibility follows the school system",bqItem:"Item",bqLimit:"Limit",bqSel:"Selected",bq1:"Credit range",bq2:"Total credits − selected",bq3:"Cross-division credits − selected",bq4:"Interest electives − selected",bq5:"Extra courses for top grades − selected",bq6:"Extra courses for transfer students − selected",bq7:"Extra courses for minor / double major − selected",bq8:"Extra courses for programs − selected",bq9:"Graduate courses taken early − selected",aiClose:"Close",fontL:"Font",fontCubic:"Cubic 11 (pixel)",fontNoto:"Noto Sans TC",fontToast:"Font: {0}",aiTitle:"AI course advisor",aiSub:"Tell it what you want to learn and it picks from courses you can take",aiDeptL:"Department to choose from",aiTextL:"Your interests or goals",aiPh:"e.g. I want to go into data analysis, learn Python and statistics, and keep Fridays free",aiGo:"Get suggestions",aiStop:"Stop",aiThinking:"Thinking. This usually takes 10 to 40 seconds…",aiNeed:"Write down your interests or goals first",aiAddAll:"Add all",aiAdd:"Add",aiAdded:"Added",aiClash:"Conflicts with your timetable",aiNone:"No courses in this department fit your timetable right now",aiErr:"Couldn't get suggestions this time. Try again later",aiDenied:"The AI service is unavailable (OpenAI key not set or out of credit)",saveErr:"Couldn't save to the server. Check your connection; it will retry on your next change",saved:"Saved automatically",aiBusy:"Too many requests. Wait a moment and try again",aiDisc:"Suggestions are AI-generated. Check them against your department's rules",aiOther:"Other dept.",aiAuto:"Auto (from your description)",aiClassify:"Working out which departments match your description…",aiPicking:"Filtered to {0}. Picking courses…",aiChip:"AI filter: {0}",aiClearT:"Clear the AI filter and show only your department",grpAi:"Courses from other departments picked by AI · {0}",aiFiltered:"Matching departments: {0}. Their courses are now in the list.",deptAria:"Select department",srcAll:"All",srcDept:"My dept.",srcGe:"Gen Ed",srcPe:"PE",srcMil:"Military",grpCls:"My class · {0}",grpSame:"Other classes in my dept.",grpViewSame:"{0}",grpViewLow:"{0} · lower years",grpLowDept:"Lower-year courses · credits count toward this term",grpGe:"General education",grpPe:"Physical education",grpMil:"Military training",autoNote2:"{0} · Required courses for your class were added ({1}). Drop any you don't need.",autoNote0:"{0} · No required courses to add for your class this term. Pick freely.",dSwitch0:"Switched to {0}. No required courses to add this term",undo:"Undo",undone:"Previous selection restored",clearQ:"Clear search",emptyQ:"No courses match \u201c{0}\u201d.",searchAll:"Search all categories",srcNote:"Offerings from the NTUB course search (Fall 2026, 4-year day program, captured 2026-10-08). Course names and instructors are shown as published.",termBreak:"Counted this term: required {0} · elective {1} · gen ed {2}",gradNeed:"{0} credits to graduate",dSwitch:"Switched to {0}. Required courses for your class added ({1})",language:"Language",appearance:"Appearance",grpMine:"{0} courses",grpLower:"Lower-year courses · credits count toward this term",grpDone:"Completed ({0})",grpShow:"Show",grpHide:"Hide",deadline:"Registration closes Oct 15 at 17:00. The system then runs the lottery and posts results",ncOn:"Showing only courses that fit your timetable",ncOff:"Showing all courses",accentToast:"Theme: {0}",themeToast:"Appearance: {0}",sep:", ",slot:"{0} P{1}–{2}",slot1:"{0} P{1}",day:"{0}"}
  };
  function tr(){return t.apply(null,arguments)}
  function t(k){var s=(STR[LANG][k]!=null?STR[LANG][k]:STR.zh[k]),a=arguments;return String(s).replace(/\{(\d)\}/g,function(_,i){return a[+i+1]})}
  var DAYS_L={zh:["","一","二","三","四","五","六","日"],en:["","Mon","Tue","Wed","Thu","Fri","Sat","Sun"]};
  var GRADE_L={zh:["","大一","大二","大三","大四"],en:["","Year 1","Year 2","Year 3","Year 4"]};
  var DEPT_EN={"全部":"All","資工":"CS","數學":"Math","物理":"Physics","國文":"Chinese","通識":"Gen Ed","外語":"Languages","體育":"PE","經濟":"Econ"};
  var TYPE_EN={"必修":"Required","選修":"Elective","通識":"Gen Ed"};
  var EN={CS101:["Intro to Programming","Lin Po-han"],MATH101:["Calculus","Chang Shu-hao"],CHI101:["Freshman Chinese","Tseng Hsiu-ling"],ENG110:["Freshman English","Emily Wang"],
    PHY111:["General Physics","Chou Ming-che"],PE102:["Badminton","Hsu Kuo-liang"],GE105:["Intro to Art","Tsai Pei-shan"],GE122:["Philosophy and Life","Wang Chih-yuan"],
    GE140:["Sustainability and Society","Cheng Ya-wen"],PE115:["Yoga","Hung Shih-han"],GE150:["Music Appreciation","Lin Yu-hsuan"],GE160:["Intro to Psychology","Kao Ming-te"],LAN120:["Beginner Japanese","Misaki Sato"],PE120:["Swimming","Hsu Kuo-liang"],CS201:["Data Structures","Chen Yi-chun"],CS230:["Computer Organization","Lin Po-han"],
    MATH201:["Linear Algebra","Chang Shu-hao"],MATH210:["Probability and Statistics","Lee Wan-jung"],ENG210:["Advanced English Reading","Sarah Collins"],ECON101:["Principles of Economics","Lu Chien-hung"],
    CS260:["Algorithm Design","Chen Yi-chun"],CS340:["Operating Systems","Huang Tzu-chien"],CS350:["Computer Networks","Yang Cheng-en"],CS318:["Intro to Machine Learning","Wu Ya-ting"],
    ENG305:["Academic Writing","David Lin"],CS420:["Information Security","Hsiao Chih-ming"],CS410:["Cloud Computing","Yang Cheng-en"],CS490:["Capstone Project","Dept. faculty"]};
  var ROOM_EN=[["資訊館","CSIE Bldg"],["理學院","Science Bldg"],["人文館","Humanities Bldg"],["語言中心","Language Ctr"],["社科館","Social Sci Bldg"],["工程二館","Eng. Bldg 2"],["體育館","Gym"],["大講堂","Auditorium"],["二樓","2F"],["舞蹈教室","Dance Studio"],["專題實驗室","Project Lab"],["藝術館","Arts Bldg"],["游泳池","Pool"]];
  function nm(c){return c.name}
  function tc(c){return c.teacher}
  function rm(c){return c.room}
  function dept(d){return LANG==="en"?DEPT_EN[d]:d}
  var RAWTYPE_EN={"專必":"Dept. req.","院必":"College req.","校必":"Univ. req.","共必":"Common req.","核必":"Core req.","通必":"Gen Ed req.","一般":"PE","專選":"Dept. elective","選修":"Elective","必選":"Req. elective"};
  function typ(x){return LANG==="en"?(TYPE_EN[x]||RAWTYPE_EN[x]||x):x}
  function deptName(d){return LANG==="en"?DEPT_EN2[d]:DEPT_ZH[d]}
  function gname(g){return GRADE_L[LANG][g]}
  function dayName(d){return t("day",DAYS_L[LANG][d])}
  function classesFor(dept,g){var l=[];COURSES.forEach(function(c){if(c.src==="dept"&&c.dept===dept&&c.grade===g&&l.indexOf(c.cls)<0)l.push(c.cls)});var O="甲乙丙丁";return l.sort(function(x,y){return O.indexOf(x.slice(-2,-1))-O.indexOf(y.slice(-2,-1))})}
  // required courses of the student's own class are added automatically; group-split project sections (A組, B組…) are left for the student to pick
  function autoReq(){
    var out=[],codes={};
    COURSES.forEach(function(c){
      if(c.src!=="dept"||c.cls!==state.cls||c.cat!=="req"||/組\)/.test(c.name)||codes[c.code])return;
      if(out.some(function(id){return overlap(byId[id],c)}))return;
      codes[c.code]=1;out.push(c.id)});
    return out}
  function initialSel(){return autoReq()}
  var state={major:"406",grade:2,cls:"",sel:[],auto:[],wait:[],src:"dept",q:"",hover:null,justAdded:null,prevCr:null,first:true,popAll:false,noClash:false,showDone:false,aiFilter:[],slot:null,phase:"register",drawing:false,results:null};
  try{var sm=localStorage.getItem("cs-major");if(DEPTS.indexOf(sm)>=0)state.major=sm}catch(e){}
  // 學號判斷出的本系與年級（伺服器解析 email，見 student_id.py）。有的話：班級與自動帶入的必修都以本系為準，
  // 學系選單只用來「查看」其他科系的課（state.major = 正在看的科系），年級按鈕隱藏
  var HOME=BOOT.student&&BOOT.student.dept&&DEPTS.indexOf(BOOT.student.dept)>=0?BOOT.student:null;
  if(HOME){state.major=HOME.dept;state.grade=HOME.grade}
  function homeDept(){return HOME?HOME.dept:state.major}
  function homeGrade(){return HOME?HOME.grade:state.grade}
  // 自動帶入的必修只看學號（科系＋年級）決定的本班；班級選單只是瀏覽，不影響帶入與存檔
  function homeCls(){return classesFor(homeDept(),homeGrade())[0]||""}
  function done(){return []}
  // graduation: NTUB requires at least 128 credits; credits earned in earlier terms are sample figures
  var GRAD_NAME={req:"必修",ele:"選修",ge:"通識"};
  function gradName(k){return typ(GRAD_NAME[k])}
  COURSES.forEach(function(c){c.min=c.grade});
  function forGrade(c){
    if(c.src==="dept")return (c.dept===state.major||state.aiFilter.indexOf(c.dept)>=0)&&c.grade<=state.grade;
    return c.grade===0||c.grade===state.grade}
  function isDone(c){return false}
  var reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
  function cardEl(id){return document.querySelector('.course[data-id="'+id+'"]')}
  function retrigger(el,cls){if(!el)return;el.classList.remove(cls);void el.offsetWidth;el.classList.add(cls)}

  var $=function(id){return document.getElementById(id)};
  var byId={};COURSES.forEach(function(c){byId[c.id]=c});
  state.cls=classesFor(homeDept(),homeGrade())[0]||"";state.sel=initialSel();state.auto=state.sel.slice();
  // 學生上次存在 Firestore 的選課（第一次登入時沒有，就用預設：本班必修自動帶入）
  (function(sv){if(!sv||DEPTS.indexOf(sv.major)<0)return;
    if(HOME){if(sv.major!==HOME.dept||+sv.grade!==HOME.grade)return} // 存檔是別的科系或年級：以學號為準重新帶入必修
    else{state.major=sv.major;state.grade=Math.min(4,Math.max(1,+sv.grade||1))}
    state.sel=(sv.sel||[]).filter(function(id){return byIdOK(id)});state.auto=(sv.auto||[]).filter(function(id){return byIdOK(id)})})(BOOT.saved);

  function seatsLeft(c){return c.cap-c.enr-(state.sel.indexOf(c.id)>=0?1:0)+0}
  // enr already excludes the student; add 1 to displayed enrolled if selected
  function enrolled(c){
    var n=c.enr+(state.sel.indexOf(c.id)>=0?1:0);
    return state.phase==="drawn"&&n>c.cap&&!c.after?c.cap:n}
  function chance(c){var n=enrolled(c);return n>c.cap?Math.round(c.cap/n*100):100}
  function overlap(a,b){
    for(var i=0;i<a.slots.length;i++)for(var j=0;j<b.slots.length;j++){
      var x=a.slots[i],y=b.slots[j];
      if(x[0]===y[0]&&x[1]<=y[2]&&y[1]<=x[2])return true}
    return false}
  function countMap(){var left=MAX,m={};state.sel.forEach(function(id){var c=byId[id].credits,k=Math.max(0,Math.min(c,left));m[id]=k;left-=k});return m}
  function counted(){return Math.min(credits(),MAX)}
  function credits(){return state.sel.reduce(function(s,id){return s+byId[id].credits},0)}
  function clashWith(c){
    for(var i=0;i<state.sel.length;i++){var o=byId[state.sel[i]];if(o.id!==c.id&&overlap(c,o))return o}
    return null}
  function missingPre(c){return c.pre.filter(function(p){return done().indexOf(p)<0})}
  function check(c){
    if(isDone(c))return {ok:false,why:t("done"),done:true};
    if(state.drawing)return {ok:false,why:t("drawing")};
    if(state.phase==="drawn"&&enrolled(c)>=c.cap)return {ok:false,why:t("noSeat")};
    var cl=clashWith(c);
    if(cl)return {ok:false,why:t("clash",nm(cl))};
    var mp=missingPre(c);
    if(mp.length)return {ok:false,why:t("pre",mp.map(function(p){return byId[p]?nm(byId[p]):p}).join(t("sep")))};
    return {ok:true}}

  function toast(msg,undo){var t=$("toast");t.textContent=msg;t.classList.toggle("act",!!undo);
    if(undo){var b=document.createElement("button");b.type="button";b.className="toast-undo";b.textContent=tr("undo");b.onclick=function(){t.classList.remove("on","act");undo()};t.appendChild(b)}
    t.classList.add("on");clearTimeout(toast.t);toast.t=setTimeout(function(){t.classList.remove("on","act")},undo?6000:2400)}
  function esc(s){return String(s).replace(/[&<>"]/g,function(m){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]})}
  // 英文單字（例如 NTUB、COURSE）各包成 .bw，任何寬度都不會從字中間斷開，只會在單字之間換行
  function keepWords(s){return esc(s).replace(/[A-Za-z0-9]+/g,function(w){return '<span class="bw">'+w+'</span>'})}

  function add(id){
    var c=byId[id],r=check(c);
    if(!r.ok){toast(t("cantAdd",r.why));retrigger(cardEl(id),"shake");return}
    state.sel.push(id);
    var en=enrolled(c);
    if(state.phase==="drawn"){c.after=true;toast(t("addedAfter",nm(c),en,c.cap))}
    else if(credits()>MAX)toast(t("regExcess",nm(c),MAX));else toast(en>c.cap?t("regOver",nm(c),en,c.cap):t("regOk",nm(c),en,c.cap))
    state.justAdded=id;
    render();
    retrigger(cardEl(id),"flash")}
  function drop(id){
    if(state.drawing)return;
    var c=byId[id],delay=reduce?0:220;
    document.querySelectorAll('.blk[data-cid="'+id+'"]').forEach(function(b){b.classList.add("out")});
    var row=document.querySelector('.mine .row[data-cid="'+id+'"]');if(row)row.classList.add("out");
    setTimeout(function(){
      state.sel=state.sel.filter(function(x){return x!==id});
      toast(state.auto.indexOf(id)>=0?t("dropReq",nm(c)):t("dropped",nm(c)));
      if(credits()<MIN)setTimeout(function(){toast(t("lowCredit",MIN))},2600);
      render()},delay)}
  function leaveWait(id){
    var row=document.querySelector('.mine .row[data-cid="'+id+'"]');if(row)row.classList.add("out");
    setTimeout(function(){state.wait=state.wait.filter(function(x){return x!==id});toast("已取消候補");render()},reduce?0:200)}

  // 選課基本資料: mirrors the school portal's quota table; personal entitlements are not in the public data, so they show "–"
  var basicOpen=false;try{basicOpen=localStorage.getItem("cs-basic")==="1"}catch(e){}
  function basicPanel(){
    var cr=credits(),n=function(f){return state.sel.filter(function(id){return f(byId[id])}).length};
    var interest=n(function(c){return /興趣/.test(c.cls)});
    var rows=[["bq1",MIN+"–"+MAX,cr],["bq2",MAX,cr],["bq3","–",0],["bq4","–",interest],["bq5","–","–"],["bq6","–","–"],["bq7","–","–"],["bq8","–","–"],["bq9","–","–"]];
    return '<details class="panel basic" id="basic"'+(basicOpen?' open':'')+'><summary><span class="basic-t">'+t("bqTitle")+'</span><span class="hint">'+t("bqHint")+'</span></summary>'+
      '<div class="bq-list">'+rows.map(function(r){var over=r[0]==="bq2"&&cr>MAX;return '<div class="bq-row'+(over?' over':'')+'"><span>'+t(r[0])+'</span><b><small>'+t("bqLimit")+'</small> '+r[1]+'</b><b><small>'+t("bqSel")+'</small> '+r[2]+'</b></div>'}).join("")+'</div></details>'}
  function renderSummary(){
    var cr=credits(),pct=Math.min(100,cr/MAX*100),minPct=MIN/MAX*100;
    var prev=state.prevCr==null?0:state.prevCr,prevPct=Math.min(100,prev/MAX*100),changed=state.prevCr!==cr;
    var oldCounts=[].map.call(document.querySelectorAll("#summary .v"),function(v){return v.firstChild?v.firstChild.nodeValue.trim():""});
    var st=cr<MIN?t("stNeed",MIN-cr):(cr>MAX?t("stOverCap",cr,cr-MAX):cr===MAX?t("stMax"):t("stLeft",MAX-cr));
    $("summary").innerHTML=
      '<div class="panel stat credit merged"><div class="m-col"><div class="cr-top">'+
      '<div><span class="k">'+t('crTitle')+'</span> <span class="v big">'+cr+' </span><small>'+t('crMax',MAX)+'</small></div>'+
      '<div class="cnt">'+t('selCount','<span class="v">'+state.sel.length+'</span>')+'</div></div>'+
      '<div class="meter'+(cr>MAX?' over':'')+'" aria-hidden="true"><i style="width:'+prevPct+'%"></i><b style="left:'+minPct+'%"></b></div>'+
      '<div class="hint '+(cr<MIN||cr>MAX?"warn":"")+'">'+st+'</div>'+
      '<div class="phase-pill '+state.phase+'">'+(state.phase==="register"?t('phase1'):t('phase3'))+'</div></div>'+
      '</div>'+basicPanel();  // 沒有接學校成績資料，不顯示畢業進度（已修學分不能用假數字）
    var sum=$("summary");
    if(!state.first)sum.classList.add("static");
    var bar=sum.querySelector(".meter i");
    requestAnimationFrame(function(){requestAnimationFrame(function(){bar.style.width=pct+"%"})});
    // count-up on the credit number, bump on any stat that changed
    var vs=sum.querySelectorAll(".v");
    vs.forEach(function(v,i){var now=v.firstChild.nodeValue.trim();if(!state.first&&oldCounts[i]!==undefined&&oldCounts[i]!==now)v.classList.add("bump")});
    if(changed&&!reduce){
      var node=vs[0].firstChild,from=prev,to=cr,t0=performance.now(),dur=state.first?700:400;
      (function step(t){var k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);node.nodeValue=Math.round(from+(to-from)*e)+" ";if(k<1)requestAnimationFrame(step)})(t0)}
    state.prevCr=cr;
    $("mini").innerHTML='<span>'+t("miniCr",'<b>'+Math.min(cr,MAX)+'</b>')+(cr>MAX?' <small class="ex">'+t("miniEx",cr-MAX)+'</small>':'')+'</span><span>'+t(state.phase==="register"?"miniReg":"miniAdm",'<b>'+state.sel.length+'</b>')+'</span><span class="mini-ph '+state.phase+'">'+t(state.phase==="register"?"miniPh1":"miniPh3")+'</span>';
    var bd=$("navBadge"),old=bd.textContent;bd.textContent=state.sel.length||"";
    if(!state.first&&old!==bd.textContent)retrigger(bd,"bump")}

  var SRC=[["all","srcAll"],["dept","srcDept"],["ge","srcGe"],["pe","srcPe"],["mil","srcMil"]];
  function renderChips(){
    var extra=state.aiFilter.filter(function(d){return d!==state.major});
    // 時段篩選時看全部類別，所以類別按鈕都不亮
    $("chips").innerHTML=SRC.map(function(x){return '<button class="chip" data-src="'+x[0]+'" aria-pressed="'+(!state.slot&&state.src===x[0])+'">'+t(x[1])+'</button>'}).join("")+
      (state.slot?'<button class="chip" id="slotClear" aria-pressed="true" title="'+t("slotClearT")+'">'+t("slotChip",slotName(state.slot))+' ✕</button>':'')+
      (extra.length?'<button class="chip chip-ai" id="aiClear" title="'+t("aiClearT")+'">'+t("aiChip",extra.map(deptName).join(t("sep")))+' ✕</button>':'')}
  function cntTag(c){var k=countMap()[c.id];if(k==null||k===c.credits)return '';return ' <span class="nocount">'+(k===0?t("tNoCount"):t("tPartial",k,c.credits))+'</span>'}
  function slotText(c){return c.slots.map(function(s){return s[1]===s[2]?t("slot1",DAYS_L[LANG][s[0]],s[1]):t("slot",DAYS_L[LANG][s[0]],s[1],s[2])}).join(t("sep"))}
  function slotName(sl){return t("slot1",DAYS_L[LANG][sl[0]],sl[1])}
  function atSlot(c,sl){return c.slots.some(function(s){return s[0]===sl[0]&&s[1]<=sl[1]&&sl[1]<=s[2]})}
  function clsShort(c){return c.src==="dept"?c.cls.replace(/^[^一二三四]+/,""):c.cls.replace(/^(通識|體育|軍訓)/,"")}

  function renderList(anim){
    var L=$("list");L.classList.remove("anim");if(anim){void L.offsetWidth;L.classList.add("anim")}
    var q=state.q.trim().toLowerCase();
    var arr=COURSES.filter(function(c){
      if(!forGrade(c))return false;
      if(state.noClash&&state.sel.indexOf(c.id)<0&&(clashWith(c)||isDone(c)))return false;
      if(state.slot){if(!atSlot(c,state.slot))return false}
      else if(state.src!=="all"&&c.src!==state.src)return false;
      if(q&&(c.name+c.code+c.teacher+c.cls).toLowerCase().indexOf(q)<0)return false;
      return true});
    // own-year courses first, then lower years; completed courses sink to the bottom
    arr.sort(function(a,b){return (b.min-a.min)||a.cls.localeCompare(b.cls)||a.code.localeCompare(b.code)||a.name.localeCompare(b.name)});
    if(!arr.length){L.innerHTML=q?'<div class="empty">'+t("emptyQ",esc(state.q.trim()))+'<div class="empty-acts">'+(state.src!=="all"?'<button type="button" class="chip" id="qAll">'+t("searchAll")+'</button>':'')+'<button type="button" class="chip" id="qClear">'+t("clearQ")+'</button></div></div>':'<div class="empty">'+(state.slot?t("slotEmpty",slotName(state.slot)):t("empty"))+'</div>';return}
    function card(c,idx){
      var sel=state.sel.indexOf(c.id)>=0,dn=isDone(c);
      var en=enrolled(c),full=en>=c.cap,over=en>c.cap,r=check(c);
      var btn,note="";
      if(sel)btn='<button class="btn drop" data-drop="'+c.id+'">'+t("bDrop")+'</button>';
      else if(dn)btn='<button class="btn ghost" disabled>'+t("bDone")+'</button>';
      else if(!r.ok){btn='<button class="btn" disabled>'+t("bAdd")+'</button>';note='<div class="note">'+esc(r.why)+'</div>'}
      else btn='<button class="btn" data-add="'+c.id+'">'+(state.phase==="register"?t("bReg"):t("bAdd"))+'</button>';
      var pct=Math.min(100,en/c.cap*100);
      var seat='<div class="seat'+(full?" full":en/c.cap>=.85?" near":"")+'" title="'+t("seatTitle")+(full?'':' · '+t("stSeats",c.cap-en))+'">'+
        '<span class="num">'+en+'<small>/'+c.cap+'</small></span>'+
        (state.phase==="register"&&en>c.cap?'<span class="st">'+t("stOver")+'</span>':full?'<span class="st">'+t("stFull")+'</span>':'')+
        '<span class="bar"><i style="width:'+pct+'%"></i></span></div>';
      return '<article class="course rk'+colIdx(c)+(sel?" sel":"")+(dn?" done":"")+'" data-id="'+c.id+'" style="--i:'+Math.min(idx,12)+'">'+
        '<span class="c-ico k'+colIdx(c)+'">'+icon(c)+'</span><div class="c-main"><h3>'+esc(nm(c))+'<span class="'+(c.cat==="req"?"req":"lvl")+'">'+typ(c.type)+'</span>'+(sel&&state.auto.indexOf(c.id)>=0?'<span class="auto">'+t("tAuto")+'</span>':'')+(sel?cntTag(c):'')+(!sel&&state.auto.indexOf(c.id)>=0?'<span class="auto off">'+t("tAutoOff")+'</span>':'')+'</h3>'+
        '<div class="meta"><span class="cls-tag">'+esc(clsShort(c))+'</span> '+esc(tc(c))+' · <span class="nw">'+slotText(c)+'</span> · <span class="nw">'+esc(rm(c))+'</span> · <span class="nw">'+t("cr",c.credits)+'</span></div>'+note+'</div>'+
        seat+btn+'</article>'}
    // 已選的課固定在最上面一組；其餘依序：my class, other classes of my year, lower years of my department, then general education, PE and military training
    var G=[["grpSel",function(c){return state.sel.indexOf(c.id)>=0}],["grpCls",function(c){return c.src==="dept"&&c.cls===state.cls},gname(state.grade)+" "+state.cls.replace(/^[^一二三四]+/,"")],
      ["grpSame",function(c){return c.src==="dept"&&c.dept===state.major&&c.grade===state.grade&&c.cls!==state.cls}],
      ["grpLowDept",function(c){return c.src==="dept"&&c.dept===state.major&&c.grade<state.grade}],
      ["grpAi",function(c){return c.src==="dept"&&c.dept!==state.major},state.aiFilter.filter(function(d){return d!==state.major}).map(deptName).join(t("sep"))],
      ["grpGe",function(c){return c.src==="ge"}],["grpPe",function(c){return c.src==="pe"}],["grpMil",function(c){return c.src==="mil"}]];
    var i=0,h="";
    function head(txt,n){return '<div class="grp"><span>'+txt+'</span><span class="grp-n">'+n+'</span></div>'}
    if(HOME&&state.major!==HOME.dept){var vn=deptName(state.major);G[2][0]="grpViewSame";G[2][2]=vn+" · "+gname(state.grade);G[3][0]="grpViewLow";G[3][2]=vn} // 查看其他科系：分組名稱不要寫「本系」
    var used={};
    G.forEach(function(g){var l=arr.filter(function(c){return !used[c.id]&&g[1](c)});l.forEach(function(c){used[c.id]=1});if(!l.length)return;h+=head(t(g[0],g[2]),l.length);h+=l.map(function(c){return card(c,i++)}).join("")});
    L.innerHTML=h}

  function renderTT(){
    var shown=state.sel.map(function(id){return byId[id]});if(state.hover&&byId[state.hover])shown=shown.concat([byId[state.hover]]);
    var maxD=5,maxP=9;shown.forEach(function(c){c.slots.forEach(function(s){maxD=Math.max(maxD,s[0]);maxP=Math.max(maxP,s[2])})});
    var tt=$("tt");tt.style.gridTemplateColumns="28px repeat("+maxD+",minmax(0,1fr))";tt.style.gridTemplateRows="28px repeat("+maxP+",44px)";
    var h='<div></div>';for(var d0=1;d0<=maxD;d0++)h+='<div class="h">'+dayName(d0)+'</div>';
    for(var p=1;p<=maxP;p++){
      h+='<div class="p" style="grid-row:'+(p+1)+';grid-column:1">'+p+'</div>';
      for(var d=1;d<=maxD;d++){var on=state.slot&&state.slot[0]===d&&state.slot[1]===p;
        h+='<button type="button" class="cell'+(on?" on":"")+'" data-slot="'+d+','+p+'" aria-pressed="'+!!on+'" aria-label="'+esc(t("cellPick",t("slot1",DAYS_L[LANG][d],p)))+'" style="grid-row:'+(p+1)+';grid-column:'+(d+1)+'"></button>'}}
    state.sel.forEach(function(id){
      var c=byId[id];
      var pop=(state.first||state.popAll||id===state.justAdded)?" pop":"";
      c.slots.forEach(function(s){h+='<button type="button" class="blk k'+colIdx(c)+pop+'" data-cid="'+id+'" data-blk="'+id+'" aria-label="'+esc(t("ttBlkAria",nm(c)))+'" style="grid-column:'+(s[0]+1)+';grid-row:'+(s[1]+1)+' / '+(s[2]+2)+'"><b>'+icon(c,"ico-s")+esc(nm(c))+'</b><span>'+esc(rm(c))+'</span></button>'})});
    if(state.hover){
      var hc=byId[state.hover];if(isDone(hc))hc=null}
    if(state.hover&&hc){var clash=!!clashWith(hc)&&state.sel.indexOf(hc.id)<0;
      if(state.sel.indexOf(hc.id)<0)hc.slots.forEach(function(s){h+='<div class="blk ghost '+(clash?"clash":"")+'" style="grid-column:'+(s[0]+1)+';grid-row:'+(s[1]+1)+' / '+(s[2]+2)+'"><b>'+esc(nm(hc))+'</b><span>'+t(clash?"gClash":"gPrev")+'</span></div>'})}
    $("tt").innerHTML=h;
    var rows=state.sel.map(function(id){var c=byId[id];return '<div class="row'+(id===state.justAdded||state.popAll?" pop":"")+'" data-cid="'+id+'"><div><span class="m-ico k'+colIdx(c)+'">'+icon(c)+'</span><b>'+esc(nm(c))+'</b>'+(state.auto.indexOf(id)>=0?' <span class="auto">'+t("tAutoS")+'</span>':'')+cntTag(c)+' <small>'+t("cr",c.credits)+' · '+slotText(c)+'</small></div><button class="btn drop" data-drop="'+id+'">'+t("bDrop")+'</button></div>'}).join("");
    rows+=state.wait.map(function(id){var c=byId[id];return '<div class="row'+(id===state.justAdded?" pop":"")+'" data-cid="'+id+'"><div><b>'+esc(c.name)+'</b> <small>候補中</small></div><button class="btn ghost" data-leave="'+id+'">取消</button></div>'}).join("");
    $("mine").innerHTML=rows||'<div class="empty">'+t("mineEmpty")+'</div>'}

  function renderGrades(){
    var ds=$("deptSel");ds.innerHTML=DEPTS.map(function(d){return '<option value="'+d+'"'+(d===state.major?' selected':'')+'>'+esc(deptName(d)+(HOME&&d===HOME.dept?t("homeTag"):""))+'</option>'}).join("");
    $("grades").innerHTML=[1,2,3,4].map(function(g){return '<button type="button" role="radio" class="seg-b" data-grade="'+g+'" aria-checked="'+(state.grade===g)+'">'+gname(g)+'</button>'}).join("");
    var cl=classesFor(homeDept(),homeGrade());$("grades").hidden=!!HOME;
    $("clsSeg").innerHTML=cl.length>1?cl.map(function(x){return '<button type="button" role="radio" class="seg-b" data-cls="'+esc(x)+'" aria-checked="'+(state.cls===x)+'">'+esc(x.replace(/^.*年/,""))+'</button>'}).join(""):"";
    $("clsSeg").hidden=cl.length<2;
    $("doneLine").innerHTML='<span class="auto-note">'+(state.auto.length?t("autoNote2",esc(state.cls),state.auto.length):t("autoNote0",esc(state.cls)))+'</span>'+t("srcNote")}
  function resetFor(msgKey){
    if(state.drawing)return;
    COURSES.forEach(function(c){c.after=false});
    var snap=resetFor.snap;resetFor.snap=null;
    var cl=classesFor(homeDept(),homeGrade());if(cl.indexOf(state.cls)<0)state.cls=cl[0]||"";
    ai.res=null;if(ai.ctl)ai.ctl.abort();
    state.sel=initialSel();state.auto=state.sel.slice();state.wait=[];state.hover=null;state.popAll=true;state.phase="register";state.results=null;
    if(msgKey){var m=state.auto.length?t(msgKey,state.cls,state.auto.length):t("dSwitch0",state.cls);
      var lost=snap&&snap.sel.filter(function(id){return snap.auto.indexOf(id)<0}).length;
      toast(m,lost?function(){state.major=snap.major;state.grade=snap.grade;state.cls=snap.cls;state.sel=snap.sel;state.auto=snap.auto;state.q=snap.q;$("q").value=snap.q;state.popAll=true;render();toast(tr("undone"))}:null)}
    render()}
  function snapshot(){resetFor.snap={major:state.major,grade:state.grade,cls:state.cls,sel:state.sel.slice(),auto:state.auto.slice(),q:state.q}}
  function renderLottery(){
    var L=$("lottery"),reg=state.sel.map(function(id){return byId[id]});
    if(state.results){
      var r=state.results,won=r.filter(function(x){return x.won===true}).length,lost=r.filter(function(x){return x.won===false}).length;
      L.innerHTML='<div class="sec-t"><h2>'+(state.drawing?t("lotDrawing"):t("lotResult"))+'</h2>'+(state.drawing?'':'<span class="hint">'+t("lotSum",won,lost)+'</span>')+'</div>'+
        '<div class="draws">'+r.map(function(x){var c=byId[x.id];
          var st=x.won==null?'<span class="dr-st spin">'+t("spin")+'</span>':x.won?'<span class="dr-st win">'+t(x.direct?"direct":"win")+'</span>':'<span class="dr-st lose">'+t("lose")+'</span>';
          return '<div class="draw'+(x.won==null?'':' rev')+'"><span class="m-ico k'+colIdx(c)+'">'+icon(c)+'</span><span class="dr-n">'+esc(nm(c))+'</span>'+st+'</div>'}).join("")+'</div>'+
        (state.drawing?'':'<div class="lot-act"><button class="btn ghost" id="resetLot" type="button">'+t("reset")+'</button><span class="hint">'+t("resetHint")+'</span></div>');
      return}
    var over=reg.filter(function(c){return enrolled(c)>c.cap});
    L.innerHTML='<div class="sec-t"><h2>'+t("regTitle")+'</h2><span class="hint">'+t("regCount",reg.length,over.length)+'</span></div>'+
      '<p class="lot-p">'+(over.length?t("overList",over.length,over.map(function(c){return esc(nm(c))+(LANG==="en"?' ('+enrolled(c)+'/'+c.cap+')':'（'+enrolled(c)+'/'+c.cap+'）')}).join(t("sep"))):t("noneOver"))+'</p>'+
      '<div class="lot-act"><span class="deadline">'+t("deadline")+'</span></div>'}
  function runLottery(){
    var list=state.sel.map(function(id){var c=byId[id];return {id:id,p:chance(c),direct:enrolled(c)<=c.cap,won:null}});
    state.drawing=true;state.results=list;state.hover=null;render();
    var step=reduce?0:520;
    list.forEach(function(x,i){setTimeout(function(){
      x.won=x.direct?true:Math.random()*100<x.p;
      renderLottery();
      if(i===list.length-1)setTimeout(finishLottery,reduce?0:450)},step*(i+1))})}
  function finishLottery(){
    var lost=state.results.filter(function(x){return !x.won}).map(function(x){return x.id});
    lost.forEach(function(id){document.querySelectorAll('.blk[data-cid="'+id+'"]').forEach(function(b){b.classList.add("out")})});
    setTimeout(function(){
      state.sel=state.sel.filter(function(id){return lost.indexOf(id)<0});
      state.drawing=false;state.phase="drawn";
      render();
      toast(lost.length?t("lotDone",lost.length):t("lotAll"))},lost.length&&!reduce?240:0)}
  function resetLottery(){
    COURSES.forEach(function(c){c.after=false});
    state.phase="register";state.results=null;state.sel=initialSel();state.auto=state.sel.slice();state.popAll=true;
    toast(t("backReg"));render()}
  function setGrade(g){if(g===state.grade||state.drawing)return;snapshot();state.grade=g;state.cls="";resetFor("dSwitch")}
  // ---------- AI advisor (uses the viewer's own Claude through the sample capability) ----------
  var ai={sample:null,dept:null,res:null,busy:false,ctl:null};
  function aiCandidates(depts){
    return COURSES.filter(function(c){
      if(state.sel.indexOf(c.id)>=0||c.credits<=0)return false;
      var ok=c.src==="dept"?(depts.indexOf(c.dept)>=0&&c.grade<=state.grade):(c.src==="ge"&&c.grade===0);
      return ok&&!clashWith(c)})}
  function aiLine(c){return [c.id,c.name,c.type,c.cls,c.teacher,slotText(c),c.credits+"學分",enrolled(c)+"/"+c.cap].join("|")}
  function renderAI(){
    $("aiFab").hidden=!ai.sample;if(!ai.sample){$("ai").hidden=true;return}
    var sel=$("aiDept"),cur=ai.dept||"auto";
    sel.innerHTML='<option value="auto"'+(cur==="auto"?' selected':'')+'>'+t("aiAuto")+'</option>'+DEPTS.map(function(d){return '<option value="'+d+'"'+(d===cur?' selected':'')+'>'+esc(deptName(d))+'</option>'}).join("");
    var out=$("aiOut");if(!ai.res){out.innerHTML="";return}
    var r=ai.res,addable=r.picks.filter(function(x){return state.sel.indexOf(x.c.id)<0&&check(x.c).ok});
    out.innerHTML=(r.depts?'<p class="ai-filtered">'+t("aiFiltered",r.depts.map(deptName).join(t("sep")))+'</p>':'')+'<p class="ai-sum">'+esc(r.summary)+'</p><div class="ai-picks">'+r.picks.map(function(x){var c=x.c,in_=state.sel.indexOf(c.id)>=0,ok=check(c).ok;
      return '<div class="ai-pick"><span class="c-ico k'+colIdx(c)+'">'+icon(c)+'</span><div class="c-main"><b>'+esc(c.name)+'</b> <span class="'+(c.cat==="req"?"req":"lvl")+'">'+typ(c.type)+'</span>'+(c.src==="dept"&&c.dept!==state.major?' <span class="lvl">'+t("aiOther")+'</span>':'')+
        '<div class="meta"><span class="cls-tag">'+esc(clsShort(c))+'</span> '+esc(c.teacher)+' · '+slotText(c)+' · '+t("cr",c.credits)+' · '+enrolled(c)+'/'+c.cap+'</div><div class="ai-why">'+esc(x.why)+'</div></div>'+
        (in_?'<button class="btn ghost" disabled>'+t("aiAdded")+'</button>':ok?'<button class="btn" data-add="'+c.id+'">'+t("aiAdd")+'</button>':'<button class="btn ghost" disabled title="'+t("aiClash")+'">'+t("aiClash")+'</button>')+'</div>'}).join("")+'</div>'+
      (r.notes.length?'<ul class="ai-notes">'+r.notes.map(function(n){return '<li>'+esc(n)+'</li>'}).join("")+'</ul>':'')+
      '<div class="ai-act">'+(addable.length>1?'<button type="button" class="btn" id="aiAll">'+t("aiAddAll")+'</button>':'')+'<span class="hint">'+t("aiDisc")+'</span></div>'}
  async function aiAsk(){
    if(ai.busy)return;
    var goal=$("aiText").value.trim(),st=$("aiStatus");
    if(!goal){st.textContent=t("aiNeed");$("aiText").focus();return}
    var choice=ai.dept||"auto",depts=[choice];
    ai.busy=true;ai.ctl=new AbortController();$("aiGo").disabled=true;$("aiStop").hidden=false;$("aiOut").innerHTML="";
    if(choice==="auto"){
      // step 1: map the student's words to departments ("財務" → 財務金融系 …) with a quick call, then filter the list to them
      st.textContent=t("aiClassify");
      try{
        var cl=await apiPost("/api/ai/depts/",{text:goal,major:homeDept()},ai.ctl.signal);
        depts=(Array.isArray(cl&&cl.depts)?cl.depts:[]).map(String).filter(function(d){return DEPTS.indexOf(d)>=0}).slice(0,3);
      }catch(e){if(e&&e.code==="cancelled"){aiDone("");return}if(e&&(e.code==="rate_limited"||e.code==="ai_unavailable")){aiFail(e.code);return}depts=[]}
      if(!depts.length)depts=[homeDept()];
      state.aiFilter=depts.slice();state.src="dept";renderChips();renderList(true);
    }
    var cands=aiCandidates(depts);
    if(!cands.length){aiDone(t("aiNone"));return}
    st.textContent=choice==="auto"?t("aiPicking",depts.map(deptName).join(t("sep"))):t("aiThinking");
    try{
      var r=await apiPost("/api/ai/suggest/",{text:goal,major:homeDept(),grade:homeGrade(),cls:state.cls,depts:depts,sel:state.sel,cands:cands.map(function(c){return c.id}).slice(0,400),lang:LANG},ai.ctl.signal);
      var byC={};cands.forEach(function(c){byC[c.id]=c});
      var picks=[],taken=[];
      (Array.isArray(r&&r.picks)?r.picks:[]).forEach(function(x){var c=byC[String(x&&x.id)];if(!c||taken.indexOf(c.id)>=0)return;taken.push(c.id);picks.push({c:c,why:String(x.reason||"")})});
      if(!picks.length)throw {code:"invalid_json"};
      ai.res={depts:choice==="auto"?depts:null,summary:String(r.summary||""),picks:picks,notes:(Array.isArray(r.notes)?r.notes:[]).map(String).filter(Boolean).slice(0,4)};
      st.textContent="";renderAI();
    }catch(e){
      var c=e&&e.code;
      if(c==="cancelled")st.textContent="";else aiFail(c);
    }finally{aiDone(null)}}
  function aiFail(c){aiDone(c==="rate_limited"?t("aiBusy"):c==="ai_unavailable"?t("aiDenied"):c==="no_candidates"?t("aiNone"):t("aiErr"))}
  function aiDone(msg){ai.busy=false;$("aiGo").disabled=false;$("aiStop").hidden=true;if(msg!=null)$("aiStatus").textContent=msg}
  function aiAddAll(){
    var added=0;ai.res.picks.forEach(function(x){var c=x.c;if(state.sel.indexOf(c.id)<0&&check(c).ok){state.sel.push(c.id);added++}});
    if(added){state.popAll=true;render();toast(tr("aiAdded")+" "+added)}}
  ai.sample=BOOT.ai?true:null; // 伺服器有設定 OPENAI_API_KEY 才顯示 AI 按鈕
  function aiOpen(open){var p=$("ai"),f=$("aiFab");p.hidden=!open;f.setAttribute("aria-expanded",open);f.classList.toggle("on",open);if(open){renderAI();setTimeout(function(){$("aiText").focus()},50)}else f.focus()}
  $("aiFab").addEventListener("click",function(){aiOpen($("ai").hidden)});
  $("aiClose").addEventListener("click",function(){aiOpen(false)});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!$("ai").hidden&&$("palPop").hidden)aiOpen(false)});
  $("aiDept").addEventListener("change",function(e){ai.dept=e.target.value});
  $("aiGo").addEventListener("click",aiAsk);
  $("aiStop").addEventListener("click",function(){if(ai.ctl)ai.ctl.abort()});
  $("aiOut").addEventListener("click",function(e){if(e.target.id==="aiAll")aiAddAll()});
  function render(){renderAI();renderGrades();renderLottery();renderSummary();renderChips();renderList(state.first||state.popAll);renderTT();state.justAdded=null;state.first=false;state.popAll=false;queueSave()}
  // ---------- Django API ----------
  function csrf(){var m=document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);return m?decodeURIComponent(m[1]):(window.APP&&APP.csrf)||""}
  async function apiPost(url,body,signal){
    var r;
    try{r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify(body),signal:signal,credentials:"same-origin"})}
    catch(e){throw {code:e&&e.name==="AbortError"?"cancelled":"network"}}
    if(r.status===401){location.href="/";throw {code:"not_signed_in"}}
    var data=await r.json().catch(function(){return {}});
    if(!r.ok)throw {code:data.error||"error"};
    return data}
  // 選課有變動就存到 Firestore（停 0.6 秒後送出，連續點很多次只會存一次）
  // 跟「資料庫裡真正存的」比，不是跟載入時的畫面比：第一次登入、或學號改了本系而重新帶入的必修，載入後就會立刻存檔
  var lastSaved=BOOT.saved?JSON.stringify({major:BOOT.saved.major,grade:BOOT.saved.grade,cls:BOOT.saved.cls,sel:BOOT.saved.sel||[],auto:BOOT.saved.auto||[]}):"",saveT=null,saving=false;
  function selPayload(){return {major:homeDept(),grade:homeGrade(),cls:homeCls(),sel:state.sel,auto:state.auto}}
  function queueSave(){if(JSON.stringify(selPayload())===lastSaved)return;clearTimeout(saveT);saveT=setTimeout(saveNow,600)}
  async function saveNow(){
    if(saving){queueSave();return}
    var p=selPayload(),key=JSON.stringify(p);if(key===lastSaved)return;
    saving=true;
    try{await apiPost("/api/selection/",p);lastSaved=key}
    catch(e){if(e.code!=="not_signed_in")toast(tr("saveErr"))}
    finally{saving=false}}
  // 關掉分頁前還沒存的變動：用 keepalive 送出，頁面關閉後請求仍會完成
  window.addEventListener("pagehide",function(){var p=selPayload();if(JSON.stringify(p)===lastSaved)return;
    try{fetch("/api/selection/",{method:"POST",keepalive:true,credentials:"same-origin",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify(p)})}catch(e){}});

  document.addEventListener("click",function(e){
    var t=e.target.closest("button");if(!t)return;
    if(t.dataset.add)add(t.dataset.add);
    else if(t.dataset.drop)drop(t.dataset.drop);
    else if(t.dataset.leave)leaveWait(t.dataset.leave);
    else if(t.dataset.grade){setGrade(+t.dataset.grade)}
    else if(t.id==="runLot"){runLottery()}
    else if(t.id==="resetLot"){resetLottery()}
    else if(t.id==="noClash"){state.noClash=!state.noClash;t.setAttribute("aria-pressed",state.noClash);renderList(true);toast(tr(state.noClash?"ncOn":"ncOff"))}
    else if(t.dataset.src){state.src=t.dataset.src;state.slot=null;renderChips();renderList(true);renderTT()}
    else if(t.dataset.blk){openDropDlg(t.dataset.blk)}
    else if(t.dataset.slot){pickSlot(t.dataset.slot.split(",").map(Number))}
    else if(t.id==="slotClear"){state.slot=null;renderChips();renderList(true);renderTT()}
    else if(t.dataset.cls){if(t.dataset.cls!==state.cls&&!state.drawing){state.cls=t.dataset.cls;state.popAll=true;render()}}
    else if(t.dataset.mv){setView(t.dataset.mv)}
    else if(t.id==="qClear"){state.q="";$("q").value="";renderList(true);$("q").focus()}
    else if(t.id==="qAll"){state.src="all";renderChips();renderList(true)}
    else if(t.id==="aiClear"){state.aiFilter=[];renderChips();renderList(true);renderAI()}
    else if(t.id==="doneTg"){state.showDone=!state.showDone;renderList(true)}});
  // 點課表上的課：跳出對話框確認要不要退選（預設焦點在「保留」）
  function openDropDlg(id){
    var c=byId[id],dlg=$("ttDlg");if(!c||state.drawing||!dlg.showModal)return;
    $("ttDlgT").textContent=nm(c);
    $("ttDlgM").innerHTML=esc(c.teacher)+' · <span class="nw">'+slotText(c)+'</span> · <span class="nw">'+esc(rm(c))+'</span> · <span class="nw">'+t("cr",c.credits)+'</span>';
    $("ttDlgW").textContent=tr("ttReqWarn");$("ttDlgW").hidden=state.auto.indexOf(id)<0;
    dlg.dataset.cid=id;dlg.returnValue="";dlg.showModal()}
  $("ttDlg").addEventListener("close",function(){var id=this.dataset.cid;if(this.returnValue==="drop"&&state.sel.indexOf(id)>=0)drop(id)});
  // 點背景關閉；點對話框本身的留白（target 也是 dialog）不算
  $("ttDlg").addEventListener("click",function(e){if(e.target!==this)return;var r=this.getBoundingClientRect();
    if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)this.close("keep")});
  // 點課表的空格：課程清單只留那個時段有上課的課（不分類別），再點一次同一格取消
  var MOBILE=window.matchMedia&&matchMedia("(max-width:720px), (max-width:1366px) and (pointer:coarse)");
  function pickSlot(sl){
    var same=state.slot&&state.slot[0]===sl[0]&&state.slot[1]===sl[1];
    state.slot=same?null:sl;renderChips();renderTT();renderList(true);
    var cell=document.querySelector('#tt [data-slot="'+sl.join(",")+'"]');if(cell)cell.focus({preventScroll:true}); // 重畫課表後保留鍵盤焦點
    if(!state.slot)return;
    if(MOBILE&&MOBILE.matches)setView("list");
    var n=document.querySelectorAll("#list .course").length;
    toast(n?t("slotToast",slotName(sl),n):t("slotEmpty",slotName(sl)));
    if(!(MOBILE&&MOBILE.matches)){var r=$("list").getBoundingClientRect();if(r.top<0||r.top>innerHeight*.6)$("chips").scrollIntoView({behavior:reduce?"auto":"smooth",block:"start"})}}
  function setView(v){
    var E=$("view-enroll"),prev=E.getAttribute("data-m");
    document.querySelectorAll(".mnav button").forEach(function(b){if(b.dataset.mv===v)b.setAttribute("aria-current","page");else b.removeAttribute("aria-current")});
    E.setAttribute("data-m",v);
    retrigger(E,"show");
    if(v==="list"&&prev!=="list")renderList(true);
    if(v==="table"){state.popAll=true;renderTT();state.popAll=false}
    try{window.scrollTo({top:0,behavior:reduce?"auto":"smooth"})}catch(e){window.scrollTo(0,0)}}
  $("deptSel").addEventListener("change",function(e){
    if(HOME){state.major=e.target.value;state.q="";$("q").value="";state.slot=null;state.popAll=true;render();
      toast(state.major===HOME.dept?tr("viewHome"):t("viewDept",deptName(state.major)));return}
    snapshot();state.major=e.target.value;state.q="";$("q").value="";state.cls="";try{localStorage.setItem("cs-major",state.major)}catch(er){}resetFor("dSwitch")});
  document.addEventListener("toggle",function(e){if(e.target.id==="basic"){basicOpen=e.target.open;try{localStorage.setItem("cs-basic",basicOpen?"1":"0")}catch(er){}}},true);
  var qT;
  $("q").addEventListener("input",function(e){state.q=e.target.value;clearTimeout(qT);qT=setTimeout(function(){renderList(true)},120)});
  $("list").addEventListener("mouseover",function(e){
    var c=e.target.closest(".course");var id=c?c.dataset.id:null;
    if(id!==state.hover){state.hover=id;renderTT()}});
  $("list").addEventListener("mouseleave",function(){if(state.hover){state.hover=null;renderTT()}});
  // accent colour presets: [name, light accent, light soft, light fg, dark accent, dark soft, dark fg]
  var ACCENTS={
    teal:["藍綠|Teal","#0e6b75","#d8eef0","#ffffff","#4cc0cc","#17383d","#06262a"],
    indigo:["靛藍|Indigo","#3f4fc4","#e2e5fb","#ffffff","#93a0ff","#252a52","#0d1033"],
    violet:["紫羅蘭|Violet","#7a3fc4","#efe4fb","#ffffff","#c59bff","#33244d","#1d0d33"],
    rose:["玫瑰|Rose","#c23a64","#fbe1ea","#ffffff","#ff8fb0","#4a1f2d","#330a18"],
    amber:["琥珀|Amber","#b05410","#fbe8d8","#ffffff","#ffa463","#46291a","#2e1300"],
    forest:["森林|Forest","#2f7a3a","#def0e0","#ffffff","#74d488","#1b3a22","#072a10"],
    ink:["墨灰|Ink","#3a4654","#e3e7ec","#ffffff","#b4c0cd","#2a333d","#11161c"],
    rainbow:["彩色|Rainbow","#6741d9","#ece7fd","#ffffff","#a98bff","#2c2450","#ffffff"]
  };
  function aName(n){var p=n.split("|");return LANG==="en"?p[1]:p[0]}
  function hexToHsl(h){var r=parseInt(h.substr(1,2),16)/255,g=parseInt(h.substr(3,2),16)/255,b=parseInt(h.substr(5,2),16)/255;
    var mx=Math.max(r,g,b),mn=Math.min(r,g,b),l=(mx+mn)/2,d=mx-mn,hh=0,ss=0;
    if(d){ss=l>.5?d/(2-mx-mn):d/(mx+mn);hh=mx===r?(g-b)/d+(g<b?6:0):mx===g?(b-r)/d+2:(r-g)/d+4;hh*=60}
    return [hh,ss*100,l*100]}
  function hsl(h,s2,l){return "hsl("+Math.round(h)+" "+Math.round(s2)+"% "+Math.round(l)+"%)"}
  function customAccent(hex){
    var c=hexToHsl(hex),h=c[0],sat=Math.min(c[1],85);
    // keep the light accent dark enough for white text, and the dark accent light enough on the dark ground
    return ["自訂",hsl(h,sat,Math.min(c[2],40)),hsl(h,Math.min(sat,70),92),"#ffffff",hsl(h,Math.min(sat,80),70),hsl(h,Math.min(sat,40),20),hsl(h,Math.min(sat,60),10)]}
  var accentKey="rose",customHex="#c23a64"; // 預設玫瑰色
  try{var sa=localStorage.getItem("cs-accent"),sc=localStorage.getItem("cs-accent-hex");if(sa&&(ACCENTS[sa]||sa==="custom"))accentKey=sa;if(sc)customHex=sc}catch(e){}
  function applyAccent(){
    var a=accentKey==="custom"?customAccent(customHex):ACCENTS[accentKey];
    var light="--accent:"+a[1]+";--accent-soft:"+a[2]+";--accent-fg:"+a[3]+";",dark="--accent:"+a[4]+";--accent-soft:"+a[5]+";--accent-fg:"+a[6]+";";
    // derive every other tint from the accent hue so status text, bars and course colours follow the chosen theme
    var hs=hexToHsl(accentKey==="custom"?customHex:a[1]),H=hs[0],S=Math.min(hs[1],80);
    light+="--ok:"+a[1]+";--ok-soft:"+a[2]+";--warn:"+hsl(H,S,30)+";--warn-soft:"+hsl(H,S*.6,88)+";";
    dark+="--ok:"+a[4]+";--ok-soft:"+a[5]+";--warn:"+hsl(H,S*.8,80)+";--warn-soft:"+hsl(H,S*.45,20)+";";
    // rainbow spreads course colours round the whole wheel instead of hugging one hue
    (accentKey==="rainbow"?[0,72,144,216,288]:[0,28,-28,56,-56]).forEach(function(dh,i){if(accentKey==="rainbow")S=85;var h2=accentKey==="rainbow"?[217,5,42,137,217][i]:(H+dh+360)%360,n=i+1;
      light+="--c"+n+":"+hsl(h2,S*.55,92)+";--c"+n+"f:"+hsl(h2,S,30)+";";
      dark+="--c"+n+":"+hsl(h2,S*.4,21)+";--c"+n+"f:"+hsl(h2,S*.75,80)+";"});
    document.documentElement.setAttribute("data-accent",accentKey);
    var st=$("accentStyle");if(!st){st=document.createElement("style");st.id="accentStyle";document.body.appendChild(st)}
    st.textContent="html:root{"+light+"}@media (prefers-color-scheme:dark){html:root:not([data-theme=\"light\"]){"+dark+"}}html:root[data-theme=\"dark\"]{"+dark+"}";
    $("swatches").innerHTML=Object.keys(ACCENTS).map(function(k){var v=ACCENTS[k];
      return '<button type="button" class="sw-b" data-accent="'+k+'" aria-pressed="'+(accentKey===k)+'" title="'+aName(v[0])+'"><span class="sw-c" style="--l:'+v[1]+';--d:'+v[4]+(k==="rainbow"?';background:conic-gradient(#1a73e8 0 25%,#d93025 0 50%,#f9ab00 0 75%,#188038 0)':'')+'"></span><span>'+aName(v[0])+'</span></button>'}).join("");
    $("palCustom").value=customHex;
    document.querySelector(".pal-custom").classList.toggle("on",accentKey==="custom")}
  function setAccent(k,hex){
    var root=document.documentElement;root.classList.add("theming");
    var was=accentKey;accentKey=k;if(hex)customHex=hex;applyAccent();if((was==="rainbow")!==(k==="rainbow"))render();
    setTimeout(function(){root.classList.remove("theming")},400);
    try{localStorage.setItem("cs-accent",k);localStorage.setItem("cs-accent-hex",customHex)}catch(e){}}
  function togglePal(open){var pop=$("palPop");if(open==null)open=pop.hidden;pop.hidden=!open;$("palBtn").setAttribute("aria-expanded",open)}
  $("palBtn").addEventListener("click",function(e){e.stopPropagation();togglePal()});
  $("palPop").addEventListener("click",function(e){e.stopPropagation();var b=e.target.closest("[data-accent]");if(b){setAccent(b.dataset.accent);toast(t("accentToast",aName(ACCENTS[b.dataset.accent][0])))}});
  $("palCustom").addEventListener("input",function(e){setAccent("custom",e.target.value)});
  document.addEventListener("click",function(){if(!$("palPop").hidden)togglePal(false)});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!$("palPop").hidden){togglePal(false);$("palBtn").focus()}});
  applyAccent();
  // theme: system -> light -> dark
  var THEMES=[["system","<svg viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" stroke-linecap=\"round\"><circle cx=\"12\" cy=\"12\" r=\"8\"/><path d=\"M12 4v16\"/><path d=\"M12 4a8 8 0 010 16z\" fill=\"currentColor\"/></svg>","themeSystem"],["light","<svg viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" stroke-linecap=\"round\"><circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4\"/></svg>","themeLight"],["dark","<svg viewBox=\"0 0 24 24\" width=\"16\" height=\"16\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" stroke-linecap=\"round\"><path d=\"M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z\"/></svg>","themeDark"]],ti=1; // 預設淺色（THEMES[1]）
  try{var saved=localStorage.getItem("cs-theme");THEMES.forEach(function(t,i){if(t[0]===saved)ti=i})}catch(e){}
  function applyTheme(){
    var t=THEMES[ti],root=document.documentElement;
    root.classList.add("theming");
    if(t[0]==="system")root.removeAttribute("data-theme");else root.setAttribute("data-theme",t[0]);
    $("themeSeg").innerHTML=THEMES.map(function(x,k){return '<button type="button" class="seg-b" data-themev="'+k+'" aria-pressed="'+(k===ti)+'" aria-label="'+tr(x[2])+'" title="'+tr(x[2])+'">'+x[1]+'</button>'}).join("");
    setTimeout(function(){root.classList.remove("theming")},400)}
  function applyStatic(){
    document.documentElement.lang=LANG==="en"?"en":"zh-Hant";
    document.title=tr("title");
    if(BOOT.name){$("hello").textContent=tr("gWelcome",BOOT.name);$("hello").hidden=false}
    var st=BOOT.student;if(st){var pg=tr("prog"+st.program);
      $("who").textContent=HOME?t("idLine",deptName(HOME.dept),pg,gname(HOME.grade),st.sid):t("idNoData",pg,st.sid);$("who").hidden=false}
    document.querySelectorAll("[data-i18n]").forEach(function(el){el.textContent=tr(el.getAttribute("data-i18n"))});
    document.querySelectorAll('[data-i18n="title"]').forEach(function(el){el.innerHTML=keepWords(tr("title"))});
    // 副標題按「 · 」分段，手機上整段一起換行
    document.querySelectorAll(".sub[data-i18n]").forEach(function(el){el.innerHTML=tr(el.getAttribute("data-i18n")).split(" · ").map(function(s){return '<span class="sub-seg">'+esc(s)+'</span>'}).join(" · ")});
    document.querySelectorAll("[data-i18n-ph]").forEach(function(el){el.placeholder=tr(el.getAttribute("data-i18n-ph"))});
    document.querySelectorAll("[data-i18n-aria]").forEach(function(el){el.setAttribute("aria-label",tr(el.getAttribute("data-i18n-aria")))});
    if(HOME)$("deptSel").setAttribute("aria-label",tr("deptViewAria"));
    document.querySelectorAll("[data-langv]").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.langv===LANG)});
    applyTheme();applyFont();if(typeof gateText==="function"&&!$("gate").hidden)gateText()}
  var FONT="cubic";try{var sf=localStorage.getItem("cs-font");if(sf==="noto"||sf==="cubic")FONT=sf}catch(e){}
  function applyFont(){
    if(FONT==="noto")document.documentElement.setAttribute("data-font","noto");else document.documentElement.removeAttribute("data-font");
    document.querySelectorAll("[data-fontv]").forEach(function(b){var k=b.dataset.fontv==="noto"?"fontNoto":"fontCubic";b.setAttribute("aria-pressed",b.dataset.fontv===FONT);b.setAttribute("aria-label",tr(k));b.title=tr(k)})}
  $("palPop").addEventListener("click",function(e){
    var fb=e.target.closest("[data-fontv]");
    if(fb){if(fb.dataset.fontv!==FONT){FONT=fb.dataset.fontv;try{localStorage.setItem("cs-font",FONT)}catch(er){}applyFont();toast(tr("fontToast",tr(FONT==="noto"?"fontNoto":"fontCubic")))}return}
    var b=e.target.closest("[data-langv],[data-themev]");if(!b)return;
    if(b.dataset.langv){if(b.dataset.langv===LANG)return;LANG=b.dataset.langv;
      try{localStorage.setItem("cs-lang",LANG)}catch(er){}
      applyStatic();applyAccent();state.popAll=true;render();toast(tr("langToast"))}
    else{ti=+b.dataset.themev;applyTheme();try{localStorage.setItem("cs-theme",THEMES[ti][0])}catch(er){}toast(tr("themeToast",tr(THEMES[ti][2])))}});
  applyTheme();
  applyStatic();
  render();
  // ---------- intro animation → sign-in → app ----------
  var SCHOOL="@ntub.edu.tw";
  function gateText(){
    var title=tr("title"),ci=0;$("gTitle").innerHTML=title.split(" ").map(function(w){return '<span class="bw">'+w.split("").map(function(ch){return '<span style="--d:'+(ci++*90)+'ms">'+esc(ch)+'</span>'}).join("")+'</span>'}).join(" ");
    $("gSub").textContent=tr("gSub");$("gH").innerHTML=keepWords(tr("gH"));$("gDesc").textContent=tr("gDesc");$("gLoginT").textContent=tr("gLogin");
    $("gNote").textContent=tr("gNote");$("gDemo").textContent=tr("gDemo");$("gSkip").textContent=tr("gSkip");
    var au=null;try{au=sessionStorage.getItem("cs-auth")}catch(e){}if(au==="demo")$("acctE").textContent=tr("gDemoChip")}
  function showLogin(){
    var g=$("gate");if(g.classList.contains("login"))return;
    g.classList.add("login");$("gCard").hidden=false;$("gSkip").hidden=true;setTimeout(function(){$("gLogin").focus()},300)}
  function enterApp(label){
    $("gOkT").textContent=label;$("gOk").hidden=false;$("gLogin").hidden=true;$("gDemo").hidden=true;$("gMsg").hidden=true;$("gNote").hidden=true;
    setTimeout(function(){var g=$("gate");g.classList.add("out");setTimeout(function(){g.hidden=true;document.body.classList.remove("gated");state.popAll=true;render()},reduce?0:600)},reduce?0:900)}
  function setAcct(email,demo){
    try{sessionStorage.setItem("cs-auth",demo?"demo":"ok")}catch(e){}
    $("acct").hidden=false;$("logoutBtn").hidden=false;$("acctE").textContent=demo?tr("gDemoChip"):email}
  $("gLogin").addEventListener("click",async function(){
    var msg=$("gMsg"),b=this;b.disabled=true;$("gLoginT").textContent=tr("gChecking");msg.hidden=true;
    var email=null;
    try{var u=window.claude&&claude.use?await claude.use("user"):null;email=u?await u.email():null}catch(e){email=null}
    b.disabled=false;$("gLoginT").textContent=tr("gLogin");
    if(email&&email.toLowerCase().slice(-SCHOOL.length)===SCHOOL){setAcct(email,false);enterApp(tr("gWelcome",email.split("@")[0]));return}
    msg.textContent=email?tr("gNotSchool",email):tr("gNoEmail");msg.hidden=false;$("gDemo").hidden=false});
  $("gDemo").addEventListener("click",function(){setAcct(null,true);enterApp(tr("gWelcomeDemo"))});
  $("gSkip").addEventListener("click",showLogin);
  function logout(){try{sessionStorage.removeItem("cs-auth");sessionStorage.setItem("cs-skipintro","1")}catch(e){}
    if(window.NTUB_SSO){apiPost("/auth/logout/",{}).catch(function(){}).then(function(){location.href="/"});return}location.reload()}
  $("acctOut").addEventListener("click",logout);$("logoutBtn").addEventListener("click",logout);
  (function(){
    // deployed behind the Google sign-in server: it already checked the @ntub.edu.tw account, so skip the preview gate
    if(window.NTUB_SSO){$("gate").hidden=true;$("acct").hidden=false;$("logoutBtn").hidden=false;
      fetch("/api/me/",{credentials:"same-origin"}).then(function(r){if(r.status===401){location.href="/";return null}return r.json()}).then(function(u){if(u)$("acctE").textContent=u.email}).catch(function(){});return}
    var auth=null;try{auth=sessionStorage.getItem("cs-auth")}catch(e){}
    gateText();
    if(auth){$("gate").hidden=true;$("acct").hidden=false;$("logoutBtn").hidden=false;$("acctE").textContent=auth==="demo"?tr("gDemoChip"):"";if(auth!=="demo"&&window.claude&&claude.use)claude.use("user").then(function(u){return u&&u.email()}).then(function(e){if(e)$("acctE").textContent=e}).catch(function(){});return}
    document.body.classList.add("gated");
    // after signing out, go straight to the sign-in card instead of replaying the intro
    var skip=null;try{skip=sessionStorage.getItem("cs-skipintro");sessionStorage.removeItem("cs-skipintro")}catch(e){}
    if(skip){$("gate").classList.add("noanim");showLogin();return}
    setTimeout(showLogin,reduce?0:2600)})();
})();
