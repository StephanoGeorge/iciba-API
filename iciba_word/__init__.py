import tempfile
from subprocess import DEVNULL, run
from typing import Any

import requests

session = requests.Session()


class Word:
    json: Any
    has_word: bool
    is_english: bool  # English or Chinese

    def __init__(self, word: str, timeout=10):
        r"""Get the translation and pronunciation and so on of the word by accessing the API"""
        self.timeout = timeout
        self.json = session.get(f'http://dict-co.iciba.com/api/dictionary.php', params={
            'type': 'json',
            'w': word,
            'key': '54A9DE969E911BC5294B70DA8ED5C9C4',  # 在网上找的 key, 似乎不限制使用频率
        }, timeout=self.timeout).json()
        self.has_word = 'word_name' in self.json
        if self.has_word:
            self.is_english = 'is_CRI' in self.json

    def __getitem__(self, item):
        return self.json[item]

    def pronounce(self, type_='am', speak=False) -> bytes:
        """
        :param type_: 'am' for American, 'en' for English, 'tts' for Text-to-Speak
        :param speak: Whether to speak
        :return Bytes of the pronunciation
        """
        if self.has_word:
            if self.is_english:
                pronunciation_name = f'pronunciation_{type_}'
                key_name = f'ph_{type_}_mp3'
            else:
                pronunciation_name = 'pronunciation_cn'
                key_name = 'symbol_mp3'
            if hasattr(self, pronunciation_name):
                return getattr(self, pronunciation_name)
            pronunciation_url = self.json['symbols'][0][key_name]
            if not pronunciation_url:
                pronunciation_url = self.json['symbols'][0]['ph_tts_mp3']
            pronunciation = session.get(pronunciation_url, timeout=self.timeout).content
            setattr(self, pronunciation_name, pronunciation)
            if speak:
                with tempfile.NamedTemporaryFile('wb', suffix='.mp3') as f:
                    f.write(pronunciation)
                    f.flush()
                    # Wait for finish. Execute through shell, or can not get the file
                    run(f'ffplay -nodisp -autoexit {f.name}', shell=True, stdout=DEVNULL, stderr=DEVNULL)
            return pronunciation
