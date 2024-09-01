from bardapi import summarizer
 
# Input text to be summarized
input_text = '''
On a sunny day, John went to the park to play baseball with his friends. He hit a home run and everyone cheered.
'''
 
# Summarize the input text with Bard-API
summary = summarizer.summarize(input_text)
 
print(summary)
# Output: "John hit a home run while playing baseball with friends at the park."
