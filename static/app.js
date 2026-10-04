const $ = (q, root=document) => root.querySelector(q);
const $$ = (q, root=document) => [...root.querySelectorAll(q)];
const faDate = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {weekday:'long', day:'numeric', month:'long'});
const faNum = new Intl.NumberFormat('fa-IR');
let step = 0;
let chosenDate = '';
let chosenTime = '';

$$('.tab').forEach(tab => tab.addEventListener('click', () => {
  $$('.tab').forEach(x => x.classList.toggle('active', x === tab));
  $$('.view').forEach(v => v.classList.toggle('hidden', v.id !== tab.dataset.view));
}));

function showStep(index) {
  const steps = $$('.step');
  step = Math.max(0, Math.min(index, steps.length - 1));
  steps.forEach((s, i) => s.classList.toggle('active', i === step));
  $$('.progress span').forEach((s, i) => s.classList.toggle('active', i <= step));
  if (step === 3) updateSummary();
}

$$('.next').forEach(btn => btn.addEventListener('click', () => {
  const current = $$('.step')[step];
  const fields = [...current.querySelectorAll('input[required]')];
  if (!fields.every(f => f.reportValidity())) return;
  showStep(step + 1);
}));
$$('.prev').forEach(btn => btn.addEventListener('click', () => showStep(step - 1)));

async function loadDates() {
  try {
    const response = await fetch('/api/dates');
    const dates = await response.json();
    const box = $('#dates'); box.classList.remove('loading'); box.innerHTML = '';
    dates.forEach(item => {
      const btn = document.createElement('button'); btn.type='button'; btn.className='choice';
      const d = new Date(item.date + 'T12:00:00');
      btn.innerHTML = `<strong>${faDate.format(d)}</strong><small>${faNum.format(item.available_count)} نوبت آزاد</small>`;
      btn.onclick = async () => {
        $$('.choice', box).forEach(x => x.classList.remove('selected')); btn.classList.add('selected');
        chosenDate = item.date; chosenTime = ''; currentNext(box).disabled = false; await loadSlots();
      }; box.appendChild(btn);
    });
    if (!dates.length) box.textContent = 'در حال حاضر روز آزادی وجود ندارد.';
  } catch { $('#dates').textContent = 'دریافت روزهای آزاد با خطا روبه‌رو شد.'; }
}

function currentNext(element) { return element.closest('.step').querySelector('.next'); }

async function loadSlots() {
  const response = await fetch(`/api/slots?day=${chosenDate}`); const data = await response.json();
  const box = $('#slots'); box.innerHTML = '';
  data.slots.forEach(value => {
    const btn = document.createElement('button'); btn.type='button'; btn.className='choice time'; btn.textContent=value;
    btn.onclick=()=>{ $$('.choice',box).forEach(x=>x.classList.remove('selected')); btn.classList.add('selected'); chosenTime=value; currentNext(box).disabled=false; };
    box.appendChild(btn);
  });
}

function updateSummary() {
  const form = $('#booking-form'); const dateText = chosenDate ? faDate.format(new Date(chosenDate+'T12:00:00')) : '';
  $('#summary').innerHTML = `<h3>خلاصه نوبت</h3><p><span>نام</span><b>${form.first_name.value} ${form.last_name.value}</b></p><p><span>روز</span><b>${dateText}</b></p><p><span>ساعت</span><b>${chosenTime}</b></p>`;
}

$('#booking-form').addEventListener('submit', async event => {
  event.preventDefault(); const form=event.currentTarget; const submit=$('button[type=submit]',form); submit.disabled=true; submit.textContent='در حال ثبت…';
  const data=new FormData(form); data.set('appointment_date',chosenDate); data.set('appointment_time',chosenTime); if(!form.consent.checked) data.set('consent','false');
  try { const response=await fetch('/api/appointments',{method:'POST',body:data}); const payload=await response.json(); if(!response.ok) throw new Error(Array.isArray(payload.detail)?payload.detail.join(' '):payload.detail);
    form.classList.add('hidden'); const a=payload.appointment; const result=$('#result'); result.classList.remove('hidden'); result.classList.add('success'); result.innerHTML=`<div class="success-icon">✓</div><h2>نوبت شما ثبت شد</h2><p>کد رهگیری را نگهداری کنید:</p><strong class="tracking">${a.tracking_code}</strong><p>${faDate.format(new Date(a.date+'T12:00:00'))}، ساعت ${a.time}</p><p>لطفاً پیش از مراجعه شرایط و مدارک لازم را بررسی کنید.</p>`;
  } catch(error) { alert(error.message); submit.disabled=false; submit.textContent='ثبت نهایی نوبت'; }
});

$('#cancel-form').addEventListener('submit', async event => { event.preventDefault(); const data=new FormData(event.currentTarget); const result=$('#cancel-result'); try { const response=await fetch('/api/appointments/cancel',{method:'POST',body:data}); const payload=await response.json(); if(!response.ok) throw new Error(payload.detail); result.className='result success'; result.textContent=payload.message; } catch(error) { result.className='result error'; result.textContent=error.message; }});

loadDates();
