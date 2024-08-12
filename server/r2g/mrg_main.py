from diagnosis_module.cxr.diagnosis import cxr_init, get_cxr_img, cxr_infer
from diagnosis_module.cxr.prompt import Prob2text
from r2g.report_generate import report_gen_cfg


class MRG:
    def __init__(self):
        self.img_model, self.img_cfg = cxr_init(
            "./diagnosis_module/cxr/config/JF.json", "./weights/JFchexpert.pth"
        )
        self.reporter = report_gen_cfg()
        self.five_diseases = {
            "Cardiac hypertrophy": 0,
            "Pulmonary edema": 1,
            "Pulmonary consolidation": 2,
            "Aatelectasis": 3,
            "Pleural effusion": 4,
        }
        # future expansion
        self.disease = {
            "Atelectasis": 0,
            "Cardiomegaly": 1,
            "Pleural_Effusion": 2,
            "Infiltration": 3,
            "Mass": 4,
            "Nodule": 5,
            "Pneumonia": 6,
            "Pneumothorax": 7,
            "Consolidation": 8,
            "Edema": 9,
            "Emphysema": 10,
            "Fibrosis": 11,
            "Pleural_Thickening": 12,
            "Hernia": 13,
        }

    def get_report(self, img_path):
        # Lesion Segmented (mimic_cxr) --> where is the disease
        img1, img2 = get_cxr_img(img_path, self.img_cfg)
        text_report = self.reporter.report(img1)[0]
        print(" text_report", text_report)

        # Disease Classifier (jfchexpert) -> prob of what disease
        prob = cxr_infer(self.img_model, img2, self.img_cfg)
        converter = Prob2text(prob, self.five_diseases)
        res = converter.get_disease_probs_from_dict()

        print("chexpert inference prob", prob)
        print("converter", converter)
        print("res", res)

        final_report = text_report + "\n" + res
        print("prompt_report", final_report)

        return final_report
