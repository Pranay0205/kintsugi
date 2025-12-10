from utils.dataset import load_joined_datasets


def analyze_command() -> None:
    data = load_joined_datasets()
    if data is None:
        return

    spring_2019 = data[data["TermID"] == "spring-2019"]

    submissions = spring_2019.to_dict(orient="records")

    print(f"\nAnalyzing {len(submissions):,} submissions from Spring 2019...")
