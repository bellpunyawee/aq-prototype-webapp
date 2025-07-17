# Adaptive Quiz System (AQS) for Construction Training

This repository contains the source code for the Adaptive Quiz System (AQS) prototype, as presented in the paper: "Adaptive Quiz for Construction Project Management Training: An Item Response Theory with Upper Confidence Bound Approach."

The AQS is a web-based application designed to provide personalized learning experiences for professionals in the construction industry. It uses an adaptive engine that integrates Item Response Theory (IRT) with the Upper Confidence Bound (UCB) algorithm to dynamically select quiz items based on each learner's estimated ability level, thereby optimizing for knowledge gain and precision.

## Features

* **Adaptive Quiz Engine:** Dynamically adjusts question difficulty based on learner performance.
* **User Authentication:** Secure login and registration for learners.
* **Quiz Interface:** Clean and simple interface for taking quizzes and viewing results.
* **Dashboard:** Allows users to track their progress and quiz history.

## Getting Started

Follow these instructions to set up and run the AQS web application on your local machine.

### Prerequisites

* Python 3.8+

### Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/aq-prototype-webapp.git
    cd aq-prototype-webapp
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    This project requires a `.env` file to store sensitive information like database credentials and the Flask secret key.

    * Create a file named `.env` in the root of the project directory.
    * Add the following configuration variables to it, replacing the placeholder values with your actual database credentials:
        ```
        DATABASE_USER=your_db_username
        DATABASE_PASSWORD=your_db_password
        DATABASE_HOST=localhost
        DATABASE_NAME=your_db_name
        SECRET_KEY=a_very_strong_and_random_secret_key
        ```

5.  **Run the application:**
    ```bash
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000`.

## Citation

If you use this code or the concepts from our work in your research, please cite our paper:

Punyawee Anunpattana, Goh Yang Miang, & Juliana Tay. (2025). Adaptive Quiz for Construction Project Management Training: An Item Response Theory with Upper Confidence Bound Approach. *Automation in Construction*.

**BibTeX:**
```bibtex
@article{Anunpattana2025AQS,
  title   = {Adaptive Quiz for Construction Project Management Training: An Item Response Theory with Upper Confidence Bound Approach},
  author  = {Anunpattana, Punyawee and Goh, Yang Miang and Tay, Juliana},
  journal = {Automation in Construction},
  year    = {2025}
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
