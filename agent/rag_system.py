import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    
    
    def __init__(self, knowledge_base_path: str = "knowledge_base/faqs.txt"):
        "made RAG with knowledge "
        logger.info("Initializing RAG Sys")
        
        logger.info("Loading sentence_transformer model")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.documents = []
        self.questions = []
        self.answers = []
        self.index = None
        
        # Load knowledge
        if os.path.exists(knowledge_base_path):
            self._load_knowledge_base(knowledge_base_path)
        else:
            logger.info(f"Knowledge base not found, creating sample")
            self._create_sample_knowledge_base(knowledge_base_path)
            self._load_knowledge_base(knowledge_base_path)
        
        logger.info("RAG System ready!\n")
    
    def _create_sample_knowledge_base(self, path: str):
        "Create FAQ knowledge"
        content = """Question: What are your business hours?
Answer: We are open Monday to Friday from 9 AM to 6 PM, and Saturday from 10 AM to 4 PM. We are closed on Sundays and public holidays.

Question: How can I contact customer support?
Answer: You can reach our customer support team via email at support@company.com, call us at 1-800-SUPPORT, or use the live chat on our website available 24/7.

Question: What products do you offer?
Answer: We offer a wide range of software solutions including project management tools, customer relationship management (CRM) systems, and data analytics platforms. All products come with a 30-day free trial.

Question: What is your return policy?
Answer: We offer a 60-day money-back guarantee on all our products. If you're not satisfied, contact our support team for a full refund, no questions asked.

Question: Do you offer training for new users?
Answer: Yes! We provide comprehensive onboarding including video tutorials, documentation, and live training sessions. Premium customers also get dedicated account managers.

Question: What payment methods do you accept?
Answer: We accept all major credit cards (Visa, MasterCard, American Express), PayPal, bank transfers, and for enterprise customers, we can arrange invoicing with net-30 terms.

Question: Is my data secure?
Answer: Absolutely. We use bank-level 256-bit encryption, regular security audits, and comply with GDPR, SOC 2, and ISO 27001 standards. Your data is backed up daily.

Question: Can I upgrade or downgrade my plan?
Answer: Yes, you can change your plan at any time. Upgrades take effect immediately, and downgrades will apply at the start of your next billing cycle. No penalties for changes.
"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Created knowledge base at {path}")
    
    def _load_knowledge_base(self, path: str):
        """Load and index knowledge base"""
        logger.info(f"Loading knowledge base from {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
       
        pairs = content.strip().split('\n\n')
        
        for pair in pairs:
            if 'Question:' in pair and 'Answer:' in pair:
                parts = pair.split('Answer:')
                question = parts[0].replace('Question:', '').strip()
                answer = parts[1].strip()
                
                self.questions.append(question)
                self.answers.append(answer)
                self.documents.append(pair)
        
        logger.info(f"✅ Loaded {len(self.questions)} Q&A pairs")
        
        # for better matching
        logger.info("creating embeddings")
        embeddings = self.model.encode(self.questions, show_progress_bar=True)
        
        # Build FAISS index
        logger.info("Building FAISS index")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
        logger.info("FAISS index built successfully")
    
    def search(self, query: str, top_k: int = 1) -> List[Tuple[int, float]]:
        """
        Search for most relevant Q&A pairs
        
        Args:
            query: User's question
            top_k: Number of results to return
            
        Returns:
            List of (index, distance) tuples
        """
        if not self.questions or self.index is None:
            return []
        
        # Embed the query
        query_embedding = self.model.encode([query])
        
        # Search in FAISS index
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'),
            top_k
        )
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.questions):
                results.append((int(idx), float(distance)))
        
        return results
    
    def get_answer(self, query: str) -> Dict[str, str]:
        """
        Get the best answer for a query
        
        Args:
            query: User's question
            
        Returns:
            Dictionary with question, answer, and confidence
        """
        results = self.search(query, top_k=1)
        
        if not results:
            return {
                'question': query,
                'answer': "I don't have information about that in my knowledge base.",
                'confidence': 0.0,
                'matched_question': None
            }
        
        idx, distance = results[0]
        
        # Lower distance = better match
        # Convert distance to confidence score (0-1)
        confidence = max(0.0, 1.0 - (distance / 10.0))
        
        return {
            'question': query,
            'answer': self.answers[idx],
            'confidence': confidence,
            'matched_question': self.questions[idx],
            'distance': distance
        }
    
    def get_context(self, query: str, top_k: int = 2) -> str:
        """
        Get formatted context for LLM
        
        Args:
            query: User's question
            top_k: Number of Q&A pairs to retrieve
            
        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return "No relevant information found in knowledge base."
        
        context_parts = []
        for i, (idx, distance) in enumerate(results, 1):
            context_parts.append(f"""Q: {self.questions[idx]}
A: {self.answers[idx]}""")
        
        return "\n\n".join(context_parts)


# Test the system
if __name__ == "__main__":
    print("="*60)
    print("RAG SYSTEM TEST")
    print("="*60 + "\n")
    
    rag = RAGSystem()
    
    test_queries = [
        "What are your business hours?",
        "How do I contact support?",
        "Is my data safe?",
        "What time do you open?",
        "Can I get my money back?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("-"*60)
        
        result = rag.get_answer(query)
        
        print(f"Matched: {result['matched_question']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"\nAnswer: {result['answer']}")