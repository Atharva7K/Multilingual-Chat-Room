
import json
words = ['Home', 'Login', 'Register', 'Logout',
        'Send', 'Enter Language', 'Submit',
        'Language field Cannot be empty',
        'Username', 'Password',
        'Remember Me', 'Sign In', 'Repeat Password', 'Please use a different username.',
        'Please use a different email address.']

# words = ['Username', 'Password',
#         'Remember Me', 'Sign In', 'Repeat Password', 'Please use a different username.',
#         'Please use a different email address.']

import googletrans
from googletrans import Translator
langs = googletrans.LANGUAGES
translator = Translator()

map = {}
for i, lang in enumerate(langs.keys()):
    print(lang)
    wordMap = {}
    for word in words:
        translated = translator.translate(word, src='en', dest=lang)
        wordMap[word] = translated.text
    map[lang] = wordMap

with open('assetMap.json', 'w') as f:
    json.dump(map, f, indent=6)
# with open('assetMap.json', 'w', encoding='utf-8') as f:
#     map = json.load(f)
# print(map)
