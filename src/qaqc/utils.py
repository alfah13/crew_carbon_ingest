from sqlalchemy import update
from datetime import datetime
import json

def validate_and_flag_data(session, table_class):
    """Run schema validation and update quality flags"""
    
    # Get records pending validation
    records = session.query(table_class).filter(
        table_class.quality_flag == 'PENDING'
    ).all()
    
    for record in records:
        errors = []
        
        # Schema validation checks
        if record.ca_downstream_mg_per_l is None:
            errors.append("Missing ca_downstream_mg_per_l")
        
        if record.actual_eff_flow_mgd and record.actual_eff_flow_mgd < 0:
            errors.append("Negative flow value")
        
        if record.date is None:
            errors.append("Missing date")
        
        # Update flag based on validation
        if errors:
            record.quality_flag = 'INVALID'
            record.validation_errors = json.dumps(errors)
        else:
            record.quality_flag = 'VALID'
            record.validation_errors = None
        
        record.validated_at = datetime.utcnow()
        record.validated_by = 'schema_validator_v1'
    
    session.commit()
    return len([r for r in records if r.quality_flag == 'VALID'])
