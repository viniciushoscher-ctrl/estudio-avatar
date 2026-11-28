// ícones Material (Apache 2.0) como no app do Gmail
const ICP = {
 mail:'M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V8l8 5 8-5v10zm-8-7L4 6h16l-8 5z',
 video:'M15 8v8H5V8h10m1-2H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4V7c0-.55-.45-1-1-1z',
 star:'M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28L12 15.4z',
 clock:'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z',
 send:'M2.01 21L23 12 2.01 3 2 10l15 2-15 2z',
 draft:'M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z',
 spam:'M15.73 3H8.27L3 8.27v7.46L8.27 21h7.46L21 15.73V8.27L15.73 3zM19 14.9L14.9 19H9.1L5 14.9V9.1L9.1 5h5.8L19 9.1v5.8zM11 7h2v6h-2zm0 8h2v2h-2z',
 trash:'M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM8 9h8v10H8V9zm7.5-5l-1-1h-5l-1 1H5v2h14V4z',
 gear:'M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46a.5.5 0 0 0-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65A.49.49 0 0 0 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1a.5.5 0 0 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.09.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z',
 help:'M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z',
 inbox:'M19 3H4.99c-1.11 0-1.98.89-1.98 2L3 19c0 1.1.88 2 1.99 2H19c1.1 0 2-.9 2-2V5c0-1.11-.9-2-2-2zm0 12h-4c0 1.66-1.35 3-3 3s-3-1.34-3-3H4.99V5H19v10z',
 tag:'M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58s1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41s-.23-1.06-.59-1.42zM13 20.01L4 11V4h7v-.01l9 9-7 7.02zM6.5 5C5.67 5 5 5.67 5 6.5S5.67 8 6.5 8 8 7.33 8 6.5 7.33 5 6.5 5z',
 people:'M16.5 13c-1.2 0-3.07.34-4.5 1-1.43-.67-3.3-1-4.5-1C5.33 13 1 14.08 1 16.25V19h22v-2.75c0-2.17-4.33-3.25-6.5-3.25zm-4 4.5h-10v-1.25c0-.54 2.56-1.75 5-1.75s5 1.21 5 1.75v1.25zm9 0H14v-1.25c0-.46-.2-.86-.52-1.22.88-.3 1.96-.53 3.02-.53 2.44 0 5 1.21 5 1.75v1.25zM7.5 12c1.93 0 3.5-1.57 3.5-3.5S9.43 5 7.5 5 4 6.57 4 8.5 5.57 12 7.5 12zm0-5.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm9 5.5c1.93 0 3.5-1.57 3.5-3.5S18.43 5 16.5 5 13 6.57 13 8.5s1.57 3.5 3.5 3.5zm0-5.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2z',
 info:'M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z',
 back:'M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z',
 archive:'M20.54 5.23l-1.39-1.68C18.88 3.21 18.47 3 18 3H6c-.47 0-.88.21-1.16.55L3.46 5.23C3.17 5.57 3 6.02 3 6.5V19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6.5c0-.48-.17-.93-.46-1.27zM6.24 5h11.52l.81.97H5.44l.8-.97zM5 19V8h14v11H5zm8.45-9h-2.9v3H8l4 4 4-4h-2.55z',
 more:'M6 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z',
 edit:'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a.996.996 0 0 0 0-1.41l-2.34-2.34a.996.996 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z'};
const IC = (n, px=24, cor='currentColor') => `<svg class="ic" width="${px}" height="${px}" viewBox="0 0 24 24"><path d="${ICP[n]}" fill="${cor}"/></svg>`;
// Telas do vídeo 2 (Gmail no iPhone + Safari na Conta Google). Caminhos e nomes conferidos na Ajuda do Gmail para
// iPhone (27/11/2026): Menu > Settings > General > Data privacy > Smart features; Data privacy > Google Workspace smart
// features > "Smart features in Google Workspace" / "Smart features in other Google products" > Done;
// Menu > Settings > Inbox > Email preferences > Images > "Ask before displaying external images".
// A ordem das outras linhas de cada tela é ilustrativa. Conta exibida: fictícia, endereço mascarado.
const C = {gray:'#8E8E93', blue:'#007AFF', red:'#FF3B30', green:'#34C759', orange:'#FF9500', purple:'#5856D6', indigo:'#5E5CE6', pink:'#FF2D55', teal:'#30B0C7', yellow:'#FFCC00', dark:'#1C1C1E', gblue:'#0B57D0'};
const AV = (l, c) => `<div class="gav" style="background:${c}">${l}</div>`;
const MAILS = [
  ['Mary Collins','8:12 AM','Sunday dinner','Bring the pie dish if you still have it...','#7B1FA2','M'],
  ['Pharmacy Rx','7:40 AM','Your prescription is ready','Pick up at the counter any time after 10...','#00897B','P'],
  ['Garden Deals Weekly','Yesterday','This week only: 40% off seeds','Spring is coming. Fill your garden for less...','#689F38','G', 'images'],
  ['First Hometown Bank','Yesterday','Urgent: your account will be locked','Dear valued customer, we noticed unusual...','#C62828','F', 'phish'],
  ['Tom (grandson)','Nov 24','Photos from the game!','Grandpa, here are the pictures I promised...','#1565C0','T'],
  ['Church Office','Nov 23','Bake sale volunteers','Thank you to everyone who signed up for...','#EF6C00','C'],
  ['Package Tracking','Nov 22','Your order has shipped','Estimated delivery: Thursday...','#5D4037','P'],
];
function inboxHTML(){
  let h = `<div class="gtop"><div class="gsearch" data-l="search"><span class="hamb" data-l="menu" data-to="drawer"><i></i><i></i><i></i></span><span class="gs-t">Search in mail</span>${AV('W','#3949AB').replace('gav','gav sm')}</div></div>
  <div class="content gcontent"><div class="glabel">Primary</div>`;
  for(const [n,t,s,p,c,l,id] of MAILS)
    h += `<div class="mrow" data-l="${n}" data-to="${id?'mail'+id:''}">${AV(l,c)}<div class="mtx"><div class="m1"><b>${n}</b><span>${t}</span></div><div class="m2">${s}</div><div class="m3">${p}</div></div><span class="star">${IC('star',24)}</span></div>`;
  h += `</div><div class="compose">${IC('edit',24)}&nbsp; Compose</div><div class="gnav"><span class="on">${IC('mail',28)}<sup>3</sup></span><span>${IC('video',28)}</span></div>
  <div class="snack" id="snack"><span>Sent</span><b data-l="Undo">Undo</b></div>`;
  return h;
}
function drawerHTML(){
  const it = (ic, l, extra='') => `<div class="ditem ${extra}" data-l="${l}" data-to="${l==='Settings'?'settings':''}"><span class="dic">${ic}</span>${l}</div>`;
  return `<div class="dshade"></div><div class="drawer"><div class="dlogo">Gmail</div>
   ${it(IC('inbox'),'All inboxes')}${it(IC('inbox'),'Primary','sel')}${it(IC('tag'),'Promotions')}${it(IC('people'),'Social')}${it(IC('info'),'Updates')}
   <div class="dhdr">All labels</div>${it(IC('star'),'Starred')}${it(IC('clock'),'Snoozed')}${it(IC('send'),'Sent')}${it(IC('draft'),'Drafts')}${it(IC('mail'),'All mail')}${it(IC('spam'),'Spam')}${it(IC('trash'),'Trash')}
   <div class="dsep"></div>${it(IC('gear'),'Settings')}${it(IC('help'),'Help & feedback')}</div>`;
}
function mailHTML(tipo){
  const top = `<div class="mtop"><span class="mback">${IC('back',26)}</span><span class="micons">${IC('archive',26)} &nbsp; ${IC('trash',26)} &nbsp; ${IC('mail',26)} &nbsp; <b data-l="dots">${IC('more',26)}</b></span></div>`;
  if(tipo === 'images') return top + `<div class="content mcont"><div class="msubj">This week only: 40% off seeds <span class="tag">Inbox</span></div>
    <div class="msend">${AV('G','#689F38')}<div><b>Garden Deals Weekly</b> <span class="mt">Yesterday</span><div class="to">to me ▾</div></div></div>
    <div class="imgbar"><span>Images are not displayed.</span><b data-l="Display images">Display images</b></div>
    <div class="ph"><div class="phi">🖼</div></div><div class="mbody">Spring is coming! Fill your garden for less with our best-selling seed packs.</div><div class="ph sm"><div class="phi">🖼</div></div></div>`;
  // e-mail falso (banco fictício)
  return top + `<div class="content mcont"><div class="msubj">Urgent: your account will be locked <span class="tag">Inbox</span></div>
    <div class="msend" data-sign="1">${AV('F','#C62828')}<div><b>First Hometown Bank</b> <span class="mt">Yesterday</span><div class="to addr">alerts@fhb-secure-48213.top</div></div></div>
    <div class="mbody"><p data-sign="2"><b>Dear valued customer,</b></p><p>We noticed unusual activity on your account.</p>
    <p data-sign="3"><b>Your account will be locked in 24 hours</b> unless you verify your details now.</p>
    <div class="fakebtn">Verify now</div><p class="sm">First Hometown Bank Security Team</p></div></div>
    <div class="pop" id="pop"><div>Mark as unread</div><div>Move to</div><div>Snooze</div><div>Change labels</div><div>Mark important</div><div>Mute</div><div>Print</div><div data-l="Report spam">Report spam</div></div>`;
}
const SAF = url => `<div class="safbar"><div class="safurl">ᴀA &nbsp;&nbsp;<span>🔒 ${url}</span>&nbsp;&nbsp; ↻</div><div class="safic">‹ &nbsp; › &nbsp; ⇪ &nbsp; ▢ &nbsp; ⧉</div></div>`;
const GA = `<div class="gahead"><span class="gat">Google Account</span>${AV('W','#3949AB').replace('gav','gav sm')}</div>`;
const TELAS = {
  home: {titulo: 'Home Screen'},
  inbox: {titulo: 'Gmail', html: inboxHTML, cls: 'gm'},
  drawer: {titulo: 'Menu', html: drawerHTML, cls: 'gm drawerv', overlay: true},
  settings: {titulo: 'Settings', voltar: '', gm: true, grupos: [
    {rows: [{l:'w••••••@gmail.com', sub:'Walt H.', ic:['#3949AB','W']}]},
    {h:'General', rows: [{l:'Notifications'}, {l:'Data privacy', to:'dataprivacy'}, {l:'Default apps'}, {l:'Hide bottom navigation', tog:false}]},
    {h:'Inbox', rows: [{l:'Inbox customizations'}, {l:'Email preferences', to:'emailprefs'}]},
    {h:'Account', rows: [{l:'Manage your Google Account'}, {l:'Vacation responder', v:'Off'}, {l:'Mobile signature'}]},
  ]},
  dataprivacy: {titulo: 'Data privacy', voltar: '', gm: true, grupos: [
    {rows: [{l:'Smart features', tog:true, sub:'Allow Gmail, Chat and Meet to use your content and activity to provide smart features'}]},
    {rows: [{l:'Google Workspace smart features', to:'workspace', sub:'Manage Workspace smart feature settings'}]},
    {rows: [{l:'Clear search history'}]},
  ]},
  workspace: {titulo: 'Google Workspace smart features', gm: true, sheet: true, grupos: [
    {rows: [{l:'Smart features in Google Workspace', tog:true, sub:'Allow Google Workspace to use your content and activity to personalize your experience across Workspace'}]},
    {rows: [{l:'Smart features in other Google products', tog:true, sub:'Allow Google products to use your Workspace content and activity to personalize your experience'}]},
  ]},
  emailprefs: {titulo: 'Email preferences', voltar: '', gm: true, grupos: [
    {rows: [{l:'Images', v:'Always display', to:'images'}, {l:'Conversation view', tog:true}, {l:'Show sender images', tog:true}]},
    {rows: [{l:'Swipe actions'}, {l:'Smart Reply', tog:true}]},
  ]},
  images: {titulo: 'Images', voltar: '', gm: true, grupos: [
    {rows: [{l:'Always display external images', chk:true}, {l:'Ask before displaying external images', chk:false}]},
  ]},
  mailimages: {titulo: 'Email', html: () => mailHTML('images'), cls: 'gm'},
  mailphish: {titulo: 'Email', html: () => mailHTML('phish'), cls: 'gm'},
  myaccount: {titulo: 'myaccount.google.com', safari: true, html: () => GA + `<div class="gatabs"><span class="on">Home</span><span>Personal info</span><span>Data &amp; privacy</span><span data-l="Security" data-to="security">Security</span></div>
    <div class="content gacont"><div class="gawel">${AV('W','#3949AB').replace('gav','gav xl')}<h3>Walt H.</h3><p>w••••••@gmail.com</p></div>
    <div class="gacard"><b>Privacy &amp; personalization</b><p>See the data in your Google Account and choose what activity is saved</p></div>
    <div class="gacard"><b>You have security tips</b><p>Security tips found in the Security Checkup</p></div></div>` + SAF('myaccount.google.com')},
  security: {titulo: 'Security', safari: true, html: () => GA + `<div class="gatabs"><span>Home</span><span>Personal info</span><span>Data &amp; privacy</span><span class="on">Security</span></div>
    <div class="content gacont"><h2 class="gah">Security</h2>
    <div class="gacard"><b>Recent security activity</b><p>No security activity or alerts in the last 28 days</p></div>
    <div class="gacard"><b>How you sign in to Google</b>
      <div class="garow" data-l="2-Step Verification"><span>2-Step Verification</span><em class="offv">✕ 2-Step Verification is off</em></div>
      <div class="garow"><span>Passkeys and security keys</span><em>Start using passkeys</em></div>
      <div class="garow"><span>Password</span><em>Last changed Mar 4</em></div>
      <div class="garow"><span>Recovery phone</span><em>(•••) •••-••68</em></div></div>
    <div class="gacard"><b>Your devices</b><p>iPhone · this device</p></div>
    <div class="gacard" data-l="Your connections to third-party apps & services"><b>Your connections to third-party apps &amp; services</b><p>Keep track of your connections to third-party apps and services</p>
      <div class="garow"><span>Coupon Saver Daily</span></div><div class="garow"><span>Word Puzzle Fun</span></div><div class="garow"><span>Recipe Box</span></div>
      <div class="galink" data-l="See all connections" data-to="connections">See all connections ›</div></div></div>` + SAF('myaccount.google.com')},
  connections: {titulo: 'Third-party connections', safari: true, html: () => GA + `<div class="content gacont"><h2 class="gah sm">Your connections to third-party apps &amp; services</h2>
    <p class="gap">You've given these apps and services access to some of your Google Account data</p>
    <div class="gacard nopad">${[['Coupon Saver Daily','#F57C00','%','coupon'],['Word Puzzle Fun','#43A047','W'],['Recipe Box','#E53935','R'],['Photo Print Shop','#1E88E5','P'],['Garden Planner','#7CB342','G']].map(([n,c,l,to]) => `<div class="garow app" data-l="${n}" data-to="${to||''}">${AV(l,c).replace('gav','gav sq')}<span>${n}</span><em>›</em></div>`).join('')}</div></div>` + SAF('myaccount.google.com')},
  coupon: {titulo: 'Coupon Saver Daily', safari: true, html: () => GA + `<div class="content gacont"><div class="gawel">${AV('%','#F57C00').replace('gav','gav xl sq')}<h3>Coupon Saver Daily</h3></div>
    <div class="gacard"><b>Access to your Google Account</b><p>Coupon Saver Daily has access to: your name, email address and profile picture</p><p>Access given on: March 2, 2021</p>
    <div class="gabtn" data-l="Remove access">Remove access</div></div></div>` + SAF('myaccount.google.com')},
};
const HOME_APPS = [
  ['FaceTime',C.green,'▶'],['Calendar','#fff','26'],['Photos','#fff','✿'],['Camera',C.gray,'◎'],
  ['Gmail','#fff','M'],['Notes',C.yellow,'✎'],['Reminders','#fff','☰'],['Clock',C.dark,'◷'],
  ['Weather',C.blue,'☁'],['Maps',C.green,'➤'],['Health','#fff','♥'],['Wallet',C.dark,'▤'],
  ['App Store',C.blue,'A'],['Books',C.orange,'▤'],['Contacts',C.gray,'☺'],['Settings','#8E8E93','⚙'],
];
