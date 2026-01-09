import logging
import os

# Application Insights integration
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace import config_integration
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer
    
    config_integration.trace_integrations(['requests', 'logging'])
    APP_INSIGHTS_ENABLED = True
except ImportError:
    APP_INSIGHTS_ENABLED = False


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(name)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Application Insights handler (if enabled)
        if APP_INSIGHTS_ENABLED:
            app_insights_key = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY') or os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
            if app_insights_key:
                try:
                    ai_handler = AzureLogHandler(connection_string=app_insights_key)
                    logger.addHandler(ai_handler)
                except Exception as e:
                    # Fallback if App Insights fails
                    logging.warning(f"Failed to initialize Application Insights: {e}")
        
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logger.setLevel(level)
    return logger


def get_tracer(name: str = 'media-platform'):
    """Get OpenCensus tracer for distributed tracing"""
    if not APP_INSIGHTS_ENABLED:
        return None
    
    app_insights_key = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY') or os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    if not app_insights_key:
        return None
    
    try:
        exporter = AzureExporter(connection_string=app_insights_key)
        sampler = ProbabilitySampler(rate=1.0)  # Sample 100% of traces
        tracer = Tracer(exporter=exporter, sampler=sampler)
        return tracer
    except Exception:
        return None



