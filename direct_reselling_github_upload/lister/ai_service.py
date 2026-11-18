"""Server-side, review-first vision draft generation. No marketplace side effects."""
import base64
import json
import os
import urllib.error
import urllib.request
from io import BytesIO
from PIL import Image, ImageOps

FIELDS = ('title','brand','item_type','gender','size','colour','keywords','description','condition_notes')
ASPECTS = ('pattern','material','fit','size_type','sleeve_length','neckline','closure','style','theme','features','vintage_status','measurements','category_suggestion','department')
SYSTEM = '''You assist a UK second-hand clothing reseller. Analyse only visible evidence and provided known facts. Never invent size, material, measurements, model, era, defects or condition. Return one JSON object with keys fields, aspects, evidence. fields keys: title, brand, item_type, gender, size, colour, keywords, description, condition_notes. aspects keys: pattern, material, fit, size_type, sleeve_length, neckline, closure, style, theme, features, vintage_status, measurements, category_suggestion, department. evidence: mapping of every populated field/aspect key to {source: visible|user|suggestion, note: short explanation}. Use empty strings for unknowns, never guesses presented as facts. Measurements must be empty unless user supplied them or a readable measurement is directly pictured. Title max 80 characters, factual and search-friendly, no keyword stuffing. Description should include title, condition, only known measurements, relevant evidence-based use, 'Ships quickly. Message for any extra details.', and SKU. Return JSON only.'''

class AIListingError(Exception):
    pass

def _image_data(photo):
    with photo.image.open('rb') as f:
        with Image.open(f) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((1600, 1600))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            output = BytesIO()
            image.save(output, format='JPEG', quality=82, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode('ascii')

def generate(item, photos):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise AIListingError('AI is not configured. Set OPENAI_API_KEY on the server.')
    if not 1 <= len(photos) <= 10:
        raise AIListingError('Select between 1 and 10 photographs.')
    facts = {k: getattr(item, k) for k in ('sku','brand','item_type','gender','size','colour','condition_notes') if getattr(item, k)}
    content = [{'type':'input_text','text':'Known user-entered item information: '+json.dumps(facts)}]
    content += [{'type':'input_image','image_url':_image_data(photo)} for photo in photos]
    payload = {'model':os.environ.get('OPENAI_MODEL','gpt-4.1-mini'), 'instructions':SYSTEM,
               'input':[{'role':'user','content':content}], 'text':{'format':{'type':'json_object'}},
               'max_output_tokens':2200}
    request = urllib.request.Request('https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = json.load(response)
    except urllib.error.HTTPError as exc:
        raise AIListingError(f'AI service returned HTTP {exc.code}. Check model access and server configuration.') from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise AIListingError('AI service could not be reached or returned an invalid response.') from exc
    texts = [part.get('text','') for message in raw.get('output',[]) for part in message.get('content',[]) if part.get('type')=='output_text']
    try:
        result = json.loads(''.join(texts))
        if not isinstance(result,dict) or not isinstance(result.get('fields'),dict) or not isinstance(result.get('aspects'),dict):
            raise ValueError('Missing draft fields')
    except (ValueError, TypeError) as exc:
        raise AIListingError('AI did not return a usable draft. Please retry.') from exc
    fields = {k: str(result['fields'].get(k) or '').strip() for k in FIELDS}
    if len(fields['title']) > 80:
        fields['title'] = fields['title'][:80].rstrip()
    for key in ('brand','item_type','gender','size','colour'):
        if facts.get(key):
            fields[key] = facts[key]  # User facts take precedence over model output.
    aspects = {k: result['aspects'].get(k) or '' for k in ASPECTS}
    evidence = result.get('evidence') if isinstance(result.get('evidence'),dict) else {}
    return {'fields':fields,'aspects':aspects,'evidence':evidence}
