# Project brief

## User and situation
# Who needs the system?-School nurses and community oral screening staff need the system. 
# What happens now, and what should become better?-Currently, oral health screening relies entirely on manual visual inspection, which is time-consuming, prone to human error, and inefficient for large-scale student group screenings. The system aims to assist staff in quickly and initially spotting potential tooth decay problems to improve screening efficiency and reduce missed checks.

## What the system should do
- Input:Close-up oral and tooth photos taken under conventional lighting
- Useful output:Clear identification of teeth with possible early or obvious decay symptoms
- Action or decision after the output:Screening staff prioritize suspected problematic teeth for further manual examination and professional dental follow-up

## Why AI may help
What pattern may need to be learned? What rules, interface, people, or review steps also belong to the system?
-Tooth decay has diverse, irregular appearances in terms of color spots, surface pits and erosion, with no fixed judgment standards for simple if/then rules. The system needs to learn visual patterns of healthy teeth and decayed teeth from real image samples. Human professional review is required for all system identification results to avoid misdiagnosis, and the system only serves as an auxiliary screening tool rather than a professional medical diagnosis tool.

## Initial data plan
- Where the data may come from:Public open-source dental image datasets with health and decay labels, plus a small number of authorized real-scene oral photos for supplementary optimization
- What we can access now: Lightweight public dental screening image datasets that are free for academic use, containing labeled healthy and decayed tooth samples
- What still needs confirmation:The exact number of valid samples, image resolution specifications, and whether supplementary scene shooting is required

## Three next actions
1. Collect and sort out open-source dental image datasets and filter valid labeled samples
2. Define clear classification standards for healthy teeth and decayed teeth for model learning
3. Clean and preprocess image data to unify basic image specifications
