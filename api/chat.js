import fs from 'fs';
import path from 'path';

const COLORS = {
  'Navy Blue': ['كحلي','كحلية','navy'], 'Midnight Blue': ['ليلي','midnight'], 'Royal Blue': ['ملكي','royal'],
  'Sky Blue': ['سماوي','sky blue'], 'Light Blue': ['أزرق فاتح','ازرق فاتح','light blue'],
  'Onyx Black': ['أونيكس','اونيكس','onyx'], 'Black': ['أسود','اسود','سودا','سوده','سودة','black'],
  'Charcoal': ['رمادي غامق','charcoal'], 'Light Grey': ['رمادي فاتح','light grey','light gray'],
  'Grey': ['رمادي','رصاصي','grey','gray'], 'White': ['أبيض','ابيض','بيضا','بيضاء','white'],
  'Beige': ['بيج','beige'], 'Camel': ['جملي','camel'], 'Brown': ['بني','brown'],
  'Oxblood': ['أوكسبلود','اوكسبلود','أحمر داكن','oxblood'], 'Burgundy': ['نبيتي','خمري','برجاندي','برغندي','burgundy'],
  'Red': ['أحمر','احمر','حمرا','حمراء','حمرة','red'], 'Emerald': ['زمردي','أخضر','اخضر','خضرا','خضراء','emerald'],
  'Pink': ['وردي','بمبي','زهري','pink'], 'Lavender': ['لافندر','lavender'], 'Champagne': ['شامبني','champagne'],
  'Gold': ['ذهبي','دهبي','gold'], 'Silver': ['فضي','فضى','silver'], 'Nude': ['نود','بيج فاتح','nude'],
};

const TYPES = [
  [['توكسيدو','tuxedo'], {name: 'Tuxedo'}], [['بدلة','بدله','suit'], {cat: 'suits'}],
  [['بليزر','blazer'], {name: 'Blazer'}], [['بالطو','معطف','overcoat','coat'], {name: 'Overcoat'}],
  [['قميص','shirt'], {name: 'Dress Shirt'}], [['بلوزة','blouse'], {name: 'Blouse'}],
  [['كوكتيل','cocktail'], {name: 'Cocktail Dress'}], [['فستان سهرة','gown','evening dress'], {name: 'Evening Gown'}],
  [['فستان','dress'], {cat: 'dresses'}], [['صندل','كعب','هيل','heel','sandal'], {name: 'Heeled'}],
  [['أوكسفورد','اوكسفورد','حذاء','جزمة','جزم','shoe','oxford'], {name: 'Oxford'}],
  [['بابيون','bow tie','bowtie'], {name: 'Bow Tie'}],
  [['كرافتة','كرافت','كرفته','جرافتة','جرافته','جرافت','قرافتة','necktie','tie'], {name: 'Silk Tie'}],
  [['حزام','belt'], {name: 'Belt'}], [['أزرار','زراير','cufflink'], {name: 'Cufflinks'}],
  [['منديل','pocket square','pocket'], {name: 'Pocket Square'}], [['إيشارب','ايشارب','وشاح','scarf'], {name: 'Scarf'}],
];

const COORD = ['تليق','يليق','تناسب','يناسب','مع ','على ','معاها','معاه',' with ',' for ','match','goes with'];
const SEL   = ['اخترت','اخترتي','اختارت','عندي','معايا','معاي','لابس','لابسة','لبست','واخد','واخده','شريت','اشتريت','اشتريتي'];
const REQ   = ['البس','هلبس','حلبس','انسب','أنسب','اقترح','اقترحلي','رشح','رشحلي','عايز','عاوز','محتاج','محتاجة','ايه','إيه','انهي','أنهي','تنصح','ينفع'];
const MEN   = ['رجالي','رجالى','رجال','راجل','رجل','ولد','شاب','عريس','men ',"men's",'male','groom','gentleman'];
const WOMEN = ['نسائي','حريمي','حريمى','نساء','امرأة','امرأه','سيدة','سيده','مدام','بنت','بنوتة','بنوته','بنوتي','انسة','آنسة','ست ','عروسة','عروسه','عروس','women','woman','female','girl','lady','bride'];
const MEN_T = ['Tuxedo','Blazer','Overcoat','Dress Shirt','Oxford','Bow Tie','Silk Tie','Belt','Cufflinks','Pocket Square'];
const WOM_T = ['Blouse','Cocktail Dress','Evening Gown','Heeled'];

function firstPos(hay, needles) {
  let min = null;
  for (const n of needles) {
    const p = hay.indexOf(n);
    if (p !== -1 && (min === null || p < min)) {
      min = p;
    }
  }
  return min;
}

function specGender(spec) {
  if (spec.cat === 'suits') return 'men';
  if (spec.cat === 'dresses') return 'women';
  const n = spec.name || '';
  if (MEN_T.includes(n)) return 'men';
  if (WOM_T.includes(n)) return 'women';
  return null;
}

function matchProducts(message, reply, all, g) {
  const msg = message.toLowerCase();
  const rep = reply.toLowerCase();
  const text = msg + ' ' + rep;
  
  const spans = [];
  const c = firstPos(msg, COORD);
  if (c !== null) spans.push([c, msg.length]);
  
  const s = firstPos(msg, SEL);
  if (s !== null) {
    let r = null;
    for (const w of REQ) {
      const p = msg.indexOf(w);
      if (p !== -1 && p > s && (r === null || p < r)) r = p;
    }
    spans.push([s, r ?? msg.length]);
  }
  
  const isCtx = (pos) => {
    for (const [a, b] of spans) {
      if (pos >= a && pos < b) return true;
    }
    return false;
  };
  
  const msgTyped = [];
  for (const [syn, spec] of TYPES) {
    const p = firstPos(msg, syn);
    if (p !== null) msgTyped.push([p, spec]);
  }
  
  let asked = msgTyped.filter(t => !isCtx(t[0]));
  if (asked.length === 0) asked = msgTyped;
  
  let specs = asked.map(t => t[1]);
  if (specs.length === 0) {
    for (const [syn, spec] of TYPES) {
      if (firstPos(text, syn) !== null) specs.push(spec);
    }
  }
  
  const colorsMap = {};
  for (const [col, syn] of Object.entries(COLORS)) {
    if (firstPos(rep, syn) !== null) colorsMap[col] = true;
    const p = firstPos(msg, syn);
    if (p !== null && !isCtx(p)) colorsMap[col] = true;
  }
  const colors = Object.keys(colorsMap);
  
  if (g === null) {
    if (firstPos(text, MEN) !== null) {
      g = 'men';
    } else if (firstPos(text, WOMEN) !== null) {
      g = 'women';
    } else {
      const gs = {};
      for (const sp of specs) {
        const x = specGender(sp);
        if (x) gs[x] = true;
      }
      const keys = Object.keys(gs);
      if (keys.length === 1) g = keys[0];
    }
  }
  
  if (specs.length === 0 && colors.length === 0) return [];
  
  const isType = (p) => {
    for (const sp of specs) {
      if (sp.cat && p.category === sp.cat) return true;
      if (sp.name && (p.name || '').includes(sp.name)) return true;
    }
    return false;
  };
  
  const genderOk = (p) => !g || [g, 'unisex'].includes(p.gender || 'unisex');
  
  const typed = all.filter(p => (specs.length === 0 || isType(p)) && genderOk(p));
  const rank = (items) => {
    items.sort((a, b) => (a.price || 0) - (b.price || 0));
    return items.slice(0, 5);
  };
  
  if (colors.length > 0) {
    const cl = typed.filter(p => colors.includes(p.color || ''));
    if (cl.length > 0) return rank(cl);
  }
  if (specs.length > 0 && typed.length > 0) return rank(typed);
  if (colors.length > 0 && specs.length === 0) {
    const cl = all.filter(p => colors.includes(p.color || '') && genderOk(p));
    if (cl.length > 0) return rank(cl);
  }
  return [];
}

function replyFromProducts(items) {
  if (items.length === 0) {
    return "I couldn't find that one just now — try a colour like navy, charcoal or burgundy, or a piece like a suit, dress, shirt or tie, and I'll show you what we have.";
  }
  const parts = [];
  for (const p of items) {
    const name = (p.name || '').split(' / ')[0];
    const price = Number(p.price || 0).toLocaleString('en-IE');
    parts.push(`the ${name} at ${p.currency || '€'} ${price}`);
  }
  let list = '';
  if (parts.length === 1) {
    list = parts[0];
  } else {
    const last = parts.pop();
    list = parts.join(', ') + ' and ' + last;
  }
  return `Lovely — here's what we have: ${list}. Grand choices, the lot of them. Would you like me to match something to go with it?`;
}

export default async function handler(req, res) {
  // CORS Configuration
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const { message, conversation_id } = req.body || {};
  const cleanMessage = (message || '').trim();
  const cid = conversation_id || `an_${Math.random().toString(36).substr(2, 9)}`;

  if (!cleanMessage) {
    return res.status(422).json({ error: 'message is required' });
  }

  // Load products catalog
  let products = [];
  try {
    const productsPath = path.join(process.cwd(), 'products.json');
    products = JSON.parse(fs.readFileSync(productsPath, 'utf8'));
  } catch (err) {
    console.error('Failed to load products.json:', err);
  }

  // Generate catalog summary for the LLM
  const byCat = {};
  for (const p of products) {
    const key = `${p.category_display || p.category || '?'} (${p.gender || 'unisex'})`;
    if (!byCat[key]) byCat[key] = {};
    byCat[key][p.color || ''] = true;
  }
  const catLines = Object.entries(byCat).map(([cat, cols]) => `${cat}: ${Object.keys(cols).join(', ')}`);
  const catalog = catLines.join('\n');

  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
  const OPENROUTER_MODEL = 'google/gemini-2.5-flash';

  const systemPrompt = `You are the Atelier Noir Concierge, a refined, friendly AI stylist for a premium formal-wear house.
Speak in warm, natural Irish English by default (polite, charming, professional, a gentle Irish warmth like 'lovely' or 'grand' used sparingly).
If the client writes in another language, reply fluently in that same language.
Write plain text only, never use markdown or symbols like _ or *.
Only mention items and colours that exist in the catalogue below; never invent products or prices.
Never mix men's and women's pieces in one look.

CLOTHING MATCHING RULES:
When the client asks what matches, goes with, or complements a specific item or color:
1. Recommend matching items that exist in our catalogue.
2. Follow classic matching guidelines:
   - Navy suit matches with white/light-blue shirts, burgundy/silver/navy ties, and black/oxblood footwear.
   - Beige suit matches with white/light-blue shirts, brown belts, and brown/tan footwear.
   - Black tuxedo matches with white dress shirts, black bow ties, and black oxford shoes.
   - For evening gowns, recommend matching accessories like pocket squares or colors for partners (e.g. emerald gown matches navy suit with emerald tie/pocket square).
3. Explain gracefully why these choices match so well in your Irish English charm.

Offer 2-3 tasteful options and keep replies short (2-4 sentences).

AVAILABLE CATALOGUE (category (gender): colours):
${catalog}`;

  let reply = '';

  if (OPENROUTER_API_KEY && OPENROUTER_API_KEY.startsWith('sk-or-')) {
    try {
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        },
        body: JSON.stringify({
          model: OPENROUTER_MODEL,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: cleanMessage }
          ],
          temperature: 0.4,
          max_tokens: 500,
        }),
      });

      if (response.ok) {
        const json = await response.json();
        reply = json.choices?.[0]?.message?.content || '';
      } else {
        console.error('OpenRouter response error:', response.status, await response.text());
      }
    } catch (err) {
      console.error('Failed to query OpenRouter:', err);
    }
  }

  // Remove markdown symbols
  reply = reply.replace(/[\*_]/g, '');

  const matched = matchProducts(cleanMessage, reply, products, null);

  if (!reply.trim()) {
    reply = replyFromProducts(matched);
  }

  const cards = matched.map((p) => ({
    id: p.id || null,
    name: p.name || '',
    price: p.price || 0,
    currency: p.currency || '€',
    color: p.color || '',
    gender: p.gender || 'unisex',
    image_url: p.image_url || '',
    category_display: p.category_display || '',
  }));

  return res.status(200).json({
    reply,
    response: reply,
    products: cards,
    conversation_id: cid,
  });
}
