from utils import *
import torch
import os
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2"
np.random.seed(2024)
torch.manual_seed(2024)

device = "cuda" if torch.cuda.is_available() else "cpu"
for i in range(torch.cuda.device_count()):
    print(f"Device {i}: {torch.cuda.get_device_name(i)}")

labels = read_txt_to_one_list('SHTech/test_100_choices_answer.txt')


def reason_mistral(choices, desc_path, rule_path):
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, low_cpu_mem_usage=True, torch_dtype=torch.float16,
                                                     device_map='auto').eval()
    preds = []
    rule = open(rule_path, "r").read()
    objects_list = read_line(desc_path)
    choices_list = read_line(choices)
    for index, obj in enumerate(objects_list):
        text = f'''You will be given an description of scene and four choices. Your task is to answer the correct choice based on the rules {rule}\n\n
                    Description: {obj[0]}\n
                    Choices: {choices_list[index][0]}\n
                    Choose just one correct answer from the options and output only the option without any explanation, please Answer:'''
        inputs = tokenizer(text, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=1000)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(answer)
        print_out = find_text_after(answer, 'please Answer:')
        print(print_out.split('.')[0])
        preds.append(print_out.split('.')[0].strip())

    return preds

def reason_gpt(choices, desc_path, rule_path):
    client = OpenAI(api_key="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")
    model_list = ["text-davinci-003", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo", "gpt-4"]
    model = model_list[2]
    preds = []
    rule = open(rule_path, "r").read()
    objects_list = read_line(desc_path)
    choices_list = read_line(choices)
    for index, obj in enumerate(objects_list):
        response = client.chat.completions.create(
            model=model,
            messages=[
                # {"role": "system",
                #  "content": f"You will be given an description of scene and four choices. Your task is to answer the correct choice based on the rules. The rules are: {rule}"},
                {"role": "system",
                 "content": f"You will be given an description of scene and four choices. Your task is to answer the correct choice"},
                {"role": "user",
                 "content": f'''Description: {obj[0]}\n
                    Choices: {choices_list[index][0]}\n
                    Choose just one correct answer from the options (A, B, C, or D) and output only without any explanation, please Answer:'''},
            ]
        )
        print(response.choices[0].message.content)
        if '.' in response.choices[0].message.content:
            preds.append(response.choices[0].message.content.split('.')[0].strip())
        else:
            preds.append(response.choices[0].message.content.strip())
        print(preds)

    return preds



# predicted_labels = reason_mistral('SHTech/test_100_choices.txt', 'SHTech/test_100_cogvlm_1_0.txt', 'rule/rule_SHTech.txt'
predicted_labels = reason_gpt('SHTech/test_100_choices.txt', 'SHTech/test_100_cogvlm_1_0.txt', 'rule/rule_SHTech.txt')

correct_predictions_incl_x = sum(1 for gt, pred in zip(labels, predicted_labels) if gt == pred)
total_predictions_incl_x = len(labels)
accuracy_incl_x = correct_predictions_incl_x / total_predictions_incl_x

# Calculate accuracy excluding 'X' labels
correct_predictions_excl_x = sum(1 for gt, pred in zip(labels, predicted_labels) if gt == pred and gt != 'X')
total_predictions_excl_x = sum(1 for gt in labels if gt != 'X')
accuracy_excl_x = correct_predictions_excl_x / total_predictions_excl_x

print(accuracy_incl_x)
print(accuracy_excl_x)

path = 'SHTech/test_100_choices_gpt_no_rule.txt'
with open(path, 'w') as file:
    for sentence in predicted_labels :
        file.write(sentence + "\n")