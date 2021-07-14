from tethys_compute.models import TethysJob
from django.http import JsonResponse


def check_status(request):
    """
    Ajax controller that checks status of condor job. If fails, return status complete because of condor file transfer
     bug. The script that follows checks for transferred file and throws error message if not there.
    Args:
        request(request): request from ajax controller
    Returns:
        JsonResponse with success and status of job
    """
    try:
        job_id = request.POST.get('workflow_id')
        job = TethysJob.objects.get_subclass(id=job_id)
        status = job.status

        return JsonResponse({'success': True, 'status': status})

    except Exception as e:
        print(e)
        return JsonResponse({'success': True, 'status': 'Complete'})
