"""
Notification Template Engine

Enterprise-grade template management with:
- Jinja2 templating
- Multi-language support
- Template versioning
- A/B testing support
- Template validation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template, TemplateError
import json
from pathlib import Path

from app.config import settings
from app.utils import logger


class TemplateEngine:
    """
    Notification template engine
    
    Features:
    - Dynamic template rendering
    - Variable validation
    - Multi-language templates
    - Template caching
    - Personalization
    """
    
    def __init__(self):
        self.template_dir = Path(settings.template_storage_path)
        self.env: Optional[Environment] = None
        self._template_cache: Dict[str, Template] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize template engine"""
        if self._initialized:
            return
        
        try:
            # Create template directory if it doesn't exist
            self.template_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Jinja2 environment
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            # Add custom filters
            self.env.filters['format_currency'] = self._format_currency
            self.env.filters['format_date'] = self._format_date
            self.env.filters['format_phone'] = self._format_phone
            
            logger.info(f"Template engine initialized with directory: {self.template_dir}")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize template engine: {e}", exc_info=True)
            raise
    
    def _format_currency(self, value: float, currency: str = 'USD') -> str:
        """Format currency filter"""
        symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹'}
        symbol = symbols.get(currency, currency)
        return f"{symbol}{value:,.2f}"
    
    def _format_date(self, value: str, format: str = '%B %d, %Y') -> str:
        """Format date filter"""
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                dt = value
            return dt.strftime(format)
        except Exception:
            return value
    
    def _format_phone(self, value: str) -> str:
        """Format phone number filter"""
        # Simple US format for example
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return value
    
    async def render_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        language: str = 'en'
    ) -> str:
        """
        Render template with variables
        
        Args:
            template_name: Template file name
            variables: Template variables
            language: Language code (e.g., 'en', 'es', 'fr')
        
        Returns:
            Rendered template string
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Add language suffix to template name
            localized_template = f"{language}/{template_name}"
            
            # Check cache first
            cache_key = f"{localized_template}:{json.dumps(variables, sort_keys=True)}"
            if cache_key in self._template_cache:
                logger.debug(f"Using cached template: {localized_template}")
                template = self._template_cache[cache_key]
            else:
                # Load template
                try:
                    template = self.env.get_template(localized_template)
                except TemplateError:
                    # Fallback to default language
                    logger.warning(f"Template not found for {language}, using default")
                    template = self.env.get_template(f"en/{template_name}")
                
                # Cache template
                self._template_cache[cache_key] = template
            
            # Render template
            rendered = template.render(**variables)
            
            logger.info(f"Template rendered: {template_name} ({language})")
            return rendered
            
        except TemplateError as e:
            logger.error(f"Template rendering error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Template error: {e}", exc_info=True)
            raise
    
    async def render_email_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        language: str = 'en',
        include_header: bool = True,
        include_footer: bool = True
    ) -> Dict[str, str]:
        """
        Render email template with header and footer
        
        Args:
            template_name: Template name
            variables: Template variables
            language: Language code
            include_header: Include email header
            include_footer: Include email footer
        
        Returns:
            Dictionary with 'html' and 'text' versions
        """
        try:
            # Render HTML template
            html_content = await self.render_template(
                f"email/{template_name}.html",
                variables,
                language
            )
            
            # Add header and footer
            if include_header:
                header = await self.render_template(
                    "email/_header.html",
                    variables,
                    language
                )
                html_content = header + html_content
            
            if include_footer:
                footer = await self.render_template(
                    "email/_footer.html",
                    variables,
                    language
                )
                html_content += footer
            
            # Render plain text version
            try:
                text_content = await self.render_template(
                    f"email/{template_name}.txt",
                    variables,
                    language
                )
            except TemplateError:
                # Generate simple text version from HTML
                text_content = self._html_to_text(html_content)
            
            return {
                "html": html_content,
                "text": text_content
            }
            
        except Exception as e:
            logger.error(f"Email template rendering error: {e}", exc_info=True)
            raise
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple version)"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except ImportError:
            # Fallback: strip HTML tags
            import re
            return re.sub('<[^<]+?>', '', html)
    
    async def create_template(
        self,
        template_name: str,
        content: str,
        language: str = 'en',
        template_type: str = 'email'
    ) -> bool:
        """
        Create new template
        
        Args:
            template_name: Template name
            content: Template content
            language: Language code
            template_type: Type (email, sms, push)
        
        Returns:
            True if created successfully
        """
        try:
            # Create language directory
            lang_dir = self.template_dir / language / template_type
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            # Write template file
            template_path = lang_dir / template_name
            template_path.write_text(content, encoding='utf-8')
            
            logger.info(f"Template created: {template_path}")
            
            # Clear cache
            self._template_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating template: {e}", exc_info=True)
            return False
    
    async def validate_template(
        self,
        content: str,
        required_variables: List[str]
    ) -> Dict[str, Any]:
        """
        Validate template syntax and variables
        
        Args:
            content: Template content
            required_variables: List of required variable names
        
        Returns:
            Validation result
        """
        try:
            # Create template from string
            template = self.env.from_string(content)
            
            # Get template variables
            template_vars = template.module.__dict__.keys()
            
            # Check required variables
            missing_vars = [var for var in required_variables if var not in template_vars]
            
            # Try rendering with dummy data
            dummy_data = {var: f"test_{var}" for var in required_variables}
            try:
                template.render(**dummy_data)
                render_valid = True
                render_error = None
            except Exception as e:
                render_valid = False
                render_error = str(e)
            
            return {
                "valid": len(missing_vars) == 0 and render_valid,
                "missing_variables": missing_vars,
                "render_error": render_error
            }
            
        except TemplateError as e:
            return {
                "valid": False,
                "syntax_error": str(e)
            }
    
    async def get_template_preview(
        self,
        template_name: str,
        sample_variables: Dict[str, Any],
        language: str = 'en'
    ) -> str:
        """
        Get template preview with sample data
        
        Args:
            template_name: Template name
            sample_variables: Sample variables for preview
            language: Language code
        
        Returns:
            Rendered preview
        """
        try:
            return await self.render_template(
                template_name,
                sample_variables,
                language
            )
        except Exception as e:
            logger.error(f"Preview generation error: {e}", exc_info=True)
            raise


# Global template engine instance
template_engine = TemplateEngine()
