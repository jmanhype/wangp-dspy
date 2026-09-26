import sys
from pathlib import Path
run_source = Path('/home/straughter/Wan2GP-story-WD-m7xw')
sys.path.insert(0, str(run_source))
from models.ltx2.ltx_core.text_encoders.gemma.tokenizer import LTXVGemmaTokenizer
path = '/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1'
wrapper = LTXVGemmaTokenizer(path, 1024, extra_special_tokens={'video_token': '<|video|>'})
vocab_size = wrapper.tokenizer.vocab_size
video_id = wrapper.tokenizer.convert_tokens_to_ids('<|video|>')
encoded = wrapper.tokenizer('<|video|> a cat walks through rain', add_special_tokens=False)['input_ids']
print(f'vocab_size={vocab_size}')
print(f'video_token_id={video_id}')
print(f'encoded={encoded}')
assert vocab_size == 262144
assert video_id == 258884
assert 258884 in encoded
print('tokenizer_check=PASS')
