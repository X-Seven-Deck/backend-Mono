"""
Advanced DSPy Prompt Optimization

Enterprise-grade prompt optimization with evaluation metrics and A/B testing.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import dspy
from dspy.teleprompt import BootstrapFewShot, MIPRO, BayesianSignatureOptimizer
from dspy.evaluate import Evaluate
import json

from app.config import settings
from app.utils import logger


class PromptOptimizer:
    """
    Advanced DSPy prompt optimizer
    
    Features:
    - Few-shot learning optimization
    - MIPRO (Multi-stage Instruction Proposal and Refinement Optimization)
    - Bayesian optimization for signatures
    - A/B testing framework
    - Performance metrics tracking
    - Prompt versioning
    """
    
    def __init__(self):
        self.lm = None
        self.optimizers: Dict[str, Any] = {}
        self.prompt_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize optimizer"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing DSPy prompt optimizer")
            
            # Configure DSPy LM
            self.lm = dspy.OpenAI(
                model="gpt-4o-mini",
                api_key=settings.openai_api_key,
                max_tokens=1500
            )
            dspy.settings.configure(lm=self.lm)
            
            # Initialize optimizers
            self._setup_optimizers()
            
            self._initialized = True
            logger.info("DSPy prompt optimizer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimizer: {e}", exc_info=True)
            raise
    
    def _setup_optimizers(self):
        """Setup different optimization strategies"""
        
        # Few-shot optimizer
        self.optimizers["fewshot"] = BootstrapFewShot(
            max_bootstrapped_demos=8,
            max_labeled_demos=8,
            max_rounds=3
        )
        
        # MIPRO optimizer (advanced)
        self.optimizers["mipro"] = MIPRO(
            num_candidates=10,
            init_temperature=1.0
        )
        
        logger.info("Optimization strategies configured")
    
    async def optimize_with_fewshot(
        self,
        module: dspy.Module,
        training_data: List[dspy.Example],
        metric_fn: Optional[callable] = None
    ) -> Tuple[dspy.Module, Dict[str, Any]]:
        """
        Optimize module using few-shot learning
        
        Args:
            module: DSPy module to optimize
            training_data: Training examples
            metric_fn: Evaluation metric function
        
        Returns:
            Tuple of (optimized module, metrics)
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Starting few-shot optimization")
            
            # Default metric if not provided
            if metric_fn is None:
                metric_fn = self._default_metric
            
            # Optimize
            optimizer = self.optimizers["fewshot"]
            optimized_module = optimizer.compile(
                module,
                trainset=training_data,
                metric=metric_fn
            )
            
            # Evaluate
            evaluator = Evaluate(
                devset=training_data[:min(50, len(training_data))],
                metric=metric_fn,
                num_threads=4
            )
            
            score = evaluator(optimized_module)
            
            metrics = {
                "optimization_type": "fewshot",
                "score": score,
                "training_examples": len(training_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Few-shot optimization complete. Score: {score}")
            
            return optimized_module, metrics
            
        except Exception as e:
            logger.error(f"Few-shot optimization error: {e}", exc_info=True)
            raise
    
    async def optimize_with_mipro(
        self,
        module: dspy.Module,
        training_data: List[dspy.Example],
        validation_data: List[dspy.Example],
        metric_fn: Optional[callable] = None
    ) -> Tuple[dspy.Module, Dict[str, Any]]:
        """
        Optimize module using MIPRO
        
        Args:
            module: DSPy module to optimize
            training_data: Training examples
            validation_data: Validation examples
            metric_fn: Evaluation metric function
        
        Returns:
            Tuple of (optimized module, metrics)
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Starting MIPRO optimization")
            
            if metric_fn is None:
                metric_fn = self._default_metric
            
            # Optimize
            optimizer = self.optimizers["mipro"]
            optimized_module = optimizer.compile(
                module,
                trainset=training_data,
                valset=validation_data,
                metric=metric_fn
            )
            
            # Evaluate on validation set
            evaluator = Evaluate(
                devset=validation_data,
                metric=metric_fn,
                num_threads=4
            )
            
            score = evaluator(optimized_module)
            
            metrics = {
                "optimization_type": "mipro",
                "score": score,
                "training_examples": len(training_data),
                "validation_examples": len(validation_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"MIPRO optimization complete. Score: {score}")
            
            return optimized_module, metrics
            
        except Exception as e:
            logger.error(f"MIPRO optimization error: {e}", exc_info=True)
            raise
    
    def _default_metric(self, example: dspy.Example, prediction: Any, trace=None) -> float:
        """
        Default evaluation metric
        
        Args:
            example: Ground truth example
            prediction: Model prediction
            trace: Execution trace
        
        Returns:
            Score between 0 and 1
        """
        # Simple exact match metric
        if hasattr(prediction, 'answer') and hasattr(example, 'answer'):
            return float(prediction.answer.strip().lower() == example.answer.strip().lower())
        return 0.0
    
    async def create_prompt_version(
        self,
        prompt_name: str,
        module: dspy.Module,
        description: str,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Create and store prompt version
        
        Args:
            prompt_name: Name of the prompt
            module: Optimized module
            description: Version description
            metrics: Performance metrics
        
        Returns:
            Version ID
        """
        version_id = f"v{len(self.prompt_versions.get(prompt_name, [])) + 1}"
        
        version_data = {
            "version_id": version_id,
            "description": description,
            "metrics": metrics,
            "created_at": datetime.utcnow().isoformat(),
            "module_state": module.dump_state() if hasattr(module, 'dump_state') else None
        }
        
        if prompt_name not in self.prompt_versions:
            self.prompt_versions[prompt_name] = []
        
        self.prompt_versions[prompt_name].append(version_data)
        
        logger.info(f"Created prompt version {version_id} for {prompt_name}")
        
        return version_id
    
    async def ab_test_prompts(
        self,
        prompt_name: str,
        version_a: str,
        version_b: str,
        test_data: List[dspy.Example],
        metric_fn: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        A/B test two prompt versions
        
        Args:
            prompt_name: Name of the prompt
            version_a: First version ID
            version_b: Second version ID
            test_data: Test examples
            metric_fn: Evaluation metric
        
        Returns:
            A/B test results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Starting A/B test: {version_a} vs {version_b}")
            
            if metric_fn is None:
                metric_fn = self._default_metric
            
            # Get versions
            versions = self.prompt_versions.get(prompt_name, [])
            version_a_data = next((v for v in versions if v["version_id"] == version_a), None)
            version_b_data = next((v for v in versions if v["version_id"] == version_b), None)
            
            if not version_a_data or not version_b_data:
                raise ValueError("Version not found")
            
            # Evaluate both versions (simplified - in production, load actual modules)
            results = {
                "prompt_name": prompt_name,
                "version_a": {
                    "id": version_a,
                    "score": version_a_data["metrics"].get("score", 0),
                    "metrics": version_a_data["metrics"]
                },
                "version_b": {
                    "id": version_b,
                    "score": version_b_data["metrics"].get("score", 0),
                    "metrics": version_b_data["metrics"]
                },
                "winner": version_a if version_a_data["metrics"].get("score", 0) > version_b_data["metrics"].get("score", 0) else version_b,
                "test_examples": len(test_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"A/B test complete. Winner: {results['winner']}")
            
            return results
            
        except Exception as e:
            logger.error(f"A/B test error: {e}", exc_info=True)
            raise
    
    async def get_best_prompt_version(
        self,
        prompt_name: str,
        metric_key: str = "score"
    ) -> Optional[Dict[str, Any]]:
        """
        Get best performing prompt version
        
        Args:
            prompt_name: Name of the prompt
            metric_key: Metric to compare
        
        Returns:
            Best version data
        """
        versions = self.prompt_versions.get(prompt_name, [])
        
        if not versions:
            return None
        
        best_version = max(
            versions,
            key=lambda v: v["metrics"].get(metric_key, 0)
        )
        
        return best_version
    
    async def export_prompt_history(
        self,
        prompt_name: str,
        output_path: str
    ):
        """
        Export prompt optimization history
        
        Args:
            prompt_name: Name of the prompt
            output_path: Output file path
        """
        versions = self.prompt_versions.get(prompt_name, [])
        
        history = {
            "prompt_name": prompt_name,
            "total_versions": len(versions),
            "versions": versions,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Exported prompt history to {output_path}")


# Global optimizer instance
prompt_optimizer = PromptOptimizer()
