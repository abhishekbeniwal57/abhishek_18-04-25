from app import create_app
from app.services.report_service import generate_report
import uuid

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        test_report_id = str(uuid.uuid4())
        print(f"Generated test report ID: {test_report_id}")
        generate_report(test_report_id, app)
        print("Report generation complete!") 