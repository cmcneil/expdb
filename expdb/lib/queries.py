from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Timecourse, Subject, Data, Modality

def _get_latest_derived_timecourse(source_timecourse: Timecourse) -> Optional[Timecourse]:
    """
    Find the most recently created timecourse that derives from the given source timecourse.
    Returns None if the timecourse has no derivatives.
    
    Parameters
    ----------
    session : Session
        SQLAlchemy session
    source_timecourse : Timecourse
        The source timecourse to trace forward from
        
    Returns
    -------
    Optional[Timecourse]
        The most recent derived timecourse, or None if there are no derivatives
    """
    # Get all timecourses that derive from this one (directly or indirectly)
    derived = []
    to_check = [source_timecourse]
    checked = set()
    
    while to_check:
        current = to_check.pop(0)
        if current.id in checked:
            continue
            
        checked.add(current.id)
        children = current.derived_timecourses.all()
        derived.extend(children)
        to_check.extend(children)
    
    if not derived:
        return None
    
    # Return the most recent one
    return max(derived, key=lambda tc: tc.date_collected)

def _find_original_upload(timecourse: Timecourse) -> Optional[Timecourse]:
    """
    Find the original upload timecourse that this timecourse derives from.
    Returns the input timecourse if it is itself an upload.
    
    Parameters
    ----------
    timecourse : Timecourse
        The timecourse to trace back to its origin
        
    Returns
    -------
    Optional[Timecourse]
        The original upload timecourse
    """
    current = timecourse
    current_modality = current.data.modality
    current_datatype = current.data.type
    while True:
        # Get all parents with matching modality and datatype
        matching_parents = []
        for parent in current.derived_from:
            if (parent.data.modality == current_modality and 
                parent.type == current_datatype):
                matching_parents.append(parent)
        
        if not matching_parents:
            return current
        current = matching_parents[0]  # Follow first parent in case of multiple parents

def get_latest_timecourses_by_modality(
    session: Session, 
    subject: Subject,
    modality: Modality
) -> List[Timecourse]:
    """
    Find all latest derived timecourses for a subject with a specific modality.
    For each original upload, finds the most recent timecourse that derives from
    the same original upload (including sister timecourses).
    
    Parameters
    ----------
    session : Session
        SQLAlchemy session
    subject : Subject
        The subject to query timecourses for
    modality : Modality
        The modality to filter by
        
    Returns
    -------
    List[Timecourse]
        List of the most recent timecourses that derive from each original upload
    """
    # Get all timecourses for this subject with the specified modality
    base_query = session.query(Timecourse).filter(
        and_(
            Timecourse.subject_id == subject.id,
            Timecourse.modality == modality
        )
    )
    
    # Find original uploads
    original_uploads = [tc for tc in base_query.all() 
                       if not tc.derived_from.count()]
    
    # Get latest derivative for each upload
    latest_timecourses = []
    for upload in original_uploads:
        # Get all timecourses that derive from this upload
        all_derived = base_query.filter(
            Timecourse.id.in_(
                tc.id for tc in base_query.all()
                if _find_original_upload(tc) == upload
            )
        ).all()
        
        if all_derived:
            # Get the most recent one
            latest = max(all_derived, key=lambda tc: tc.date_collected)
            latest_timecourses.append(latest)
        else:
            # If no derivatives, include the original upload
            latest_timecourses.append(upload)
            
    return latest_timecourses