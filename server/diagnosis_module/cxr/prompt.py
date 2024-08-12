from torch import Tensor


class Prob2text:
    def __init__(self, prob: Tensor, disease: dict):
        self.prob = prob.squeeze().detach().cpu().numpy()
        self.disease = disease
        self.level_prompt = {
            "0": "No sign of",
            "1": "Small possibility of",
            "2": "Patient is likely to have",
            "3": "Definitely have",
        }
        self.grade = self.grading()
        self.prompt_head = "Higher disease score means higher possibility of illness.\n"

    def grading(self):
        level = {
            "0": [],
            "1": [],
            "2": [],
            "3": [],
        }
        for k in self.disease.keys():
            score = self.prob[self.disease[k]]
            if 0 <= score < 0.2:
                level["0"].append(k)
            elif 0.2 <= score < 0.5:
                level["1"].append(k)
            elif 0.5 <= score < 0.9:
                level["2"].append(k)
            elif score >= 0.9:
                level["3"].append(k)
        return level

    @staticmethod
    def disease_retrieval(namelist: list):
        diseases = ""
        for j in namelist:
            diseases += j
            diseases += ", "
        diseases = diseases[:-2]
        return diseases

    # def prompt_a(self):
    #     prompt_a = self.prompt_head + "Network A: "
    #     for k in self.disease.keys():
    #         prompt_a += f"{k} score: {self.prob[self.disease[k]]:.3f}, "
    #     prompt_a = prompt_a[:-2] + "."
    #     return prompt_a

    def get_disease_probs_from_dict(self):
        level = self.grade
        prompt_b = ""

        for l in level.keys():
            if len(level[l]) == 0:
                continue
            diseases = self.disease_retrieval(level[l])
            prompt_b += f"{self.level_prompt[l]} {diseases}."

        return prompt_b
