from .auth import AuthModel
from .nav import NavModel
from .academics import (
    AcademicsModel, InfrastructureModel, ClassificationModel, CourseModel, 
    StudentConfigModel, ActivityCertificateModel, CourseActivityModel, 
    PackageMasterModel, BoardMasterModel, CertificateMasterModel, 
    PgsCourseLimitModel, SeatDetailModel, AdmissionModel, AdvisoryModel, 
    StudentModel, CourseAllocationModel, ResearchModel, ThesisModel, AdvisoryStatusModel, IGradeModel, BatchModel,
    AdvisorApprovalModel, TeacherApprovalModel, EventModel, EventAssignmentModel, SemesterRegistrationModel,
    CounsellingModel, PaperUploadModel, MessagingModel, StudentExtensionModel, MiscAcademicsModel, RecheckingModel,
    RevisedResultModel, ExtensionManagementModel, AdvisorAllocationModel, DswApprovalModel, LibraryApprovalModel, FeeApprovalModel, DeanApprovalModel, DeanPgsApprovalModel
)

# Explicit exports (defensive): prevents missing-name ImportError if the grouped import list above is edited/merged incorrectly.
from .academics import FeeApprovalModel as FeeApprovalModel, DeanApprovalModel as DeanApprovalModel, DeanPgsApprovalModel as DeanPgsApprovalModel
from .leave import LeaveModel, HolidayModel, LeaveEncashmentModel, LeaveReportModel, LeaveConfigModel, LeaveAssignmentModel, WeeklyOffModel, LeaveTypeModel
from .hrms import (
    LoanModel, IncomeTaxModel, EmployeePortalModel, EmployeeModel, DesignationCategoryModel,
    EmployeeDocumentModel, EmployeeQualificationModel, EmployeePermissionModel, 
    EmployeeFamilyModel, EmployeeNomineeModel, EmployeeBookModel, LTCModel,
    PreviousJobModel, ForeignVisitModel, TrainingModel, DeptExamModel,
    ServiceVerificationModel, SARModel, FirstAppointmentModel, IncrementModel,
    NoDuesModel, EarnedLeaveModel, DisciplinaryModel, BookGrantModel, BonusModel,
    PropertyReturnModel
)
from .establishment_promotion import AppointingAuthorityModel, NonTeachingPromotionModel
from .payroll import PayrollModel
from .establishment import EstablishmentModel
from .examination import ExaminationModel
