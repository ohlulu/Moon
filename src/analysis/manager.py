import logging
from typing import Dict, Any, List, Type
from datetime import datetime
from .base import BaseAnalyzer
from .technical import TechnicalAnalyzer
from .sentiment import SentimentAnalyzer
from .risk import RiskAnalyzer
from ..database.mongodb import MongoDB

logger = logging.getLogger(__name__)

class AnalysisManager:
    """Manager for market analysis."""
    
    def __init__(self):
        """Initialize analysis manager."""
        self.db = MongoDB.get_database()
        self._analyzers: Dict[str, BaseAnalyzer] = {}
        self._register_default_analyzers()
    
    def _register_default_analyzers(self):
        """Register default analyzers."""
        self.register_analyzer('technical', TechnicalAnalyzer())
        self.register_analyzer('sentiment', SentimentAnalyzer())
        self.register_analyzer('risk', RiskAnalyzer())
    
    def register_analyzer(self, name: str, analyzer: BaseAnalyzer):
        """
        Register a new analyzer.
        
        Args:
            name: Unique name for the analyzer
            analyzer: The analyzer instance
        """
        if not isinstance(analyzer, BaseAnalyzer):
            raise ValueError(
                f"Analyzer must inherit from BaseAnalyzer: {analyzer}"
            )
        
        if name in self._analyzers:
            logger.warning(f"Overwriting existing analyzer: {name}")
        
        self._analyzers[name] = analyzer
        logger.info(f"Registered analyzer: {name}")
    
    def unregister_analyzer(self, name: str):
        """
        Unregister an analyzer.
        
        Args:
            name: Name of the analyzer to unregister
        """
        if name in self._analyzers:
            del self._analyzers[name]
            logger.info(f"Unregistered analyzer: {name}")
        else:
            logger.warning(f"Analyzer not found: {name}")
    
    async def analyze_market(
        self,
        pair_symbol: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform market analysis using all registered analyzers.
        
        Args:
            pair_symbol: Trading pair symbol
            data: Market data for analysis
            
        Returns:
            Dict containing analysis results from all analyzers
        """
        try:
            results = {}
            summaries = []
            
            # Run all analyzers
            for name, analyzer in self._analyzers.items():
                # Check if required data is available
                required_data = analyzer.get_analysis_requirements()
                if not all(key in data for key in required_data):
                    logger.warning(
                        f"Skipping {name} analyzer: missing required data"
                    )
                    continue
                
                # Run analysis
                analysis = await analyzer.analyze(data)
                results[name] = analysis
                summaries.append(analysis['summary'])
            
            # Prepare analysis document
            analysis_doc = {
                'pair_symbol': pair_symbol,
                'timestamp': datetime.utcnow(),
                'analyzers': list(results.keys()),
                'results': results,
                'summary': " || ".join(summaries)
            }
            
            # Store in database
            await self.store_analysis(analysis_doc)
            
            return analysis_doc
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            raise
    
    async def store_analysis(self, analysis_data: Dict[str, Any]):
        """Store analysis results in database."""
        try:
            await self.db.market_analysis.update_one(
                {
                    'pair_symbol': analysis_data['pair_symbol'],
                    'timestamp': analysis_data['timestamp']
                },
                {'$set': analysis_data},
                upsert=True
            )
            
            logger.info(f"Stored analysis for {analysis_data['pair_symbol']}")
            
        except Exception as e:
            logger.error(f"Error storing analysis: {str(e)}")
            raise
    
    async def get_latest_analysis(
        self,
        pair_symbol: str
    ) -> Dict[str, Any]:
        """Get latest analysis results for a trading pair."""
        try:
            analysis = await self.db.market_analysis.find_one(
                {'pair_symbol': pair_symbol},
                sort=[('timestamp', -1)]
            )
            return analysis
            
        except Exception as e:
            logger.error(
                f"Error fetching latest analysis for {pair_symbol}: {str(e)}"
            )
            raise
    
    def get_analyzer_info(self, name: str) -> Dict[str, str]:
        """
        Get information about an analyzer.
        
        Args:
            name: Name of the analyzer
            
        Returns:
            Dict containing analyzer information
        """
        if name not in self._analyzers:
            raise KeyError(f"Analyzer not found: {name}")
            
        analyzer = self._analyzers[name]
        return {
            'name': name,
            'type': analyzer.__class__.__name__,
            'description': analyzer.description,
            'requirements': analyzer.get_analysis_requirements()
        }
    
    def list_analyzers(self) -> List[str]:
        """
        Get list of registered analyzer names.
        
        Returns:
            List of analyzer names
        """
        return list(self._analyzers.keys()) 