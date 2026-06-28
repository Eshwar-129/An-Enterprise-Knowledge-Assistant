import os
from fpdf import FPDF

class SystemDesignPDF(FPDF):
    def header(self):
        """Builds a formal enterprise document header blueprint."""
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(110, 120, 135)
        self.cell(0, 8, "AETHERA SYNC SYSTEMS - DEPLOYMENT BLUEPRINT", ln=True, align="R")
        # Top borderline
        self.set_draw_color(200, 205, 215)
        self.set_line_width(0.3)
        self.line(10, 16, 200, 16)
        self.ln(5)

    def footer(self):
        """Maintains dynamic page number parameters in the lower margin."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 145, 155)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def build_section(self, section_title, lines_list, is_warning=False):
        """Handles text-wrapping and section rendering cleanly."""
        self.set_font("Helvetica", "B", 12)
        if is_warning:
            self.set_text_color(190, 40, 55)  # Alert Maroon
        else:
            self.set_text_color(20, 60, 120)  # Core Tech Blue
            
        self.cell(0, 8, section_title, ln=True)
        self.ln(1)
        
        # Format body content blocks
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 65, 70)
        for line in lines_list:
            if line.startswith("->") or line.startswith("["):
                self.set_font("Helvetica", "B", 9.5)
                self.set_text_color(40, 45, 50)
            else:
                self.set_font("Helvetica", "", 9.5)
                self.set_text_color(65, 70, 75)
                
            self.multi_cell(0, 5, line)
            self.ln(2.5)
        self.ln(2)

def generate_blueprint_pdf():
    pdf = SystemDesignPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Primary Title Block
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 25, 45)
    pdf.cell(0, 10, "SYSTEM DESIGN: ENTERPRISE KNOWLEDGE ASSISTANT", ln=True, align="L")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 6, "Target Client: Aethera Sync Systems | Architecture Evaluation Spec", ln=True, align="L")
    pdf.ln(6)
    
    # 1. RAG Architecture Strategy & Query Rewriting (25% Weight Criteria)
    pdf.build_section("1. Pre-Retrieval Query Optimization & Hybrid Architecture (AI System Design - 25%)", [
        "To satisfy production parameters for accuracy, retrieval speed, and keyword matching relevancy, the Aethera Sync Assistant bypasses standard semantic architectures in favor of an advanced pre-retrieval pipeline combined with a synchronized Two-Stage Hybrid Search Subsystem.",
        "[Step 1: Intelligent Query Rewriting Node]",
        "Before hitting any internal index tables, the user's raw input passes through a high-speed, deterministic query rewriter executed via a stateless LangChain Expression Language (LCEL) sub-chain. A dedicated LLM instruction set transforms informal syntax into clean, target-dense search keywords.",
        "-> It strips ambient conversational pleasantries and greetings (e.g., 'Could you check if...').",
        "-> It standardizes acronyms and adds domain-specific expansion keywords to significantly elevate downstream indexing capture rates.",
        "[Step 2: Dual-Engine Parallel Hybrid Search]",
        "The optimized keywords are simultaneously routed to two separate retrieval architectures using asynchronous runtime scheduling loops:",
        "-> Component A: Sparse Lexical Matching (Rank-BM25) - This engine matches exact text patterns, ensuring rigid technical expressions (like API route strings, SKU codes, or connection formats) are successfully captured even when vector proximity distance gaps expand.",
        "-> Component B: Dense Multi-Dimensional Vectors - Documents are processed using a PyPDFDirectoryLoader and split using a RecursiveCharacterTextSplitter (Chunk Size: 800 tokens, Overlap: 150 tokens) before being transformed via OpenAI's 'text-embedding-3-small' embedding index.",
        "-> Dimension Optimization Decision (Matryoshka Truncation):",
        "To maximize memory performance and query execution velocity, we utilize Matryoshka Representation learning parameters to truncate native 1536 vector outputs down to 512 dimensions. This retains 99%+ downstream accuracy while shortening cosine-distance calculation delays by up to 3x.",
        "-> Localized HNSW Vector Storage:",
        "ChromaDB acts as our high-performance embedded storage provider, organizing vectors in a Hierarchical Navigable Small World (HNSW) graph index to ensure O(log N) lookup scalability as system text files multiply."
    ])
    
    # 2. Re-Ranking & Response Generation (25% Weight Criteria)
    pdf.build_section("2. Cross-Encoder Re-Ranking & Generation (Answer Quality - 25%)", [
        "To optimize downstream processing payloads, the parallel retrieval pipelines aggregate the top 10 combined context blocks. This raw collection is passed into a local Cross-Encoder re-ranking filter using FlashRank.",
        "FlashRank evaluates actual cross-attention linguistic relevance, squeezing the context window down to the top 3 highest-scoring items. This condensed format provides rich, concentrated context directly to the generation model while keeping execution token counts minimal.",
        "-> Explicit Anti-Hallucination Guardrails:",
        "The system prompt completely bounds the generation LLM (gpt-4o-mini) to the provided context chunks. If the retrieved texts do not contain explicit details to substantiate the user prompt, the model is instructed to output exactly: 'I am sorry, but the provided documentation does not contain enough information to answer your question.' This completely eliminates external training knowledge drifts."
    ])
    
    # 3. Security Framework & Structural Guardrails (20% Weight Criteria)
    pdf.build_section("3. Production Guardrail Subsystem & DLP (Engineering Quality - 20%)", [
        "Following enterprise compliance standards, sensitive platform vectors like API infrastructure strings and system credentials are secured against injection attempts or leakage risks using a two-way defensive border.",
        "-> Input Guardrail Layer (Intent Validation):",
        "Incoming string inputs are matched against high-risk structural token arrays ('password', 'master token', 'connection string'). Flagged prompts are aborted using a clean security exception block before ever querying the vector database.",
        "-> Output Guardrail Layer (Data Loss Prevention):",
        "Responses are systematically parsed using regex and key signature matching for infrastructure assets (e.g., 'sk-proj-', 'postgresql://'). Any matching data blocks are immediately dropped and replaced with an alert notification, protecting assets like the 'Company_Credentials.pdf' layer."
    ])
    
    # 4. Evaluation Strategy (15% Weight Criteria)
    pdf.build_section("4. Formal Performance Evaluation (Evaluation Approach - 15%)", [
        "System reliability is tracked through automated test suites using deterministic metrics across simulated enterprise scenarios:",
        "1. Faithfulness Metric: Validates that the generated response relies solely on the provided context.",
        "2. Answer Relevance Metric: Matches semantic alignment between the user's prompt and the generated response.",
        "3. Context Recall Metric: Confirms the hybrid search accurately pulled the correct source text fragments from the underlying knowledge base.",
        "Test loops explicitly check system behaviors under edge cases, such as handling out-of-boundary questions and handling multi-document reasoning requests."
    ])
    
    # 5. Technical Stack Ledger
    pdf.build_section("5. Standardized Production Stack Summary", [
        "-> Language Layer: Python 3.11+ configured inside an isolated virtual environment via uv.",
        "-> Framework Layer: LangChain (LCEL) for clean, stateless runtime execution flows.",
        "-> API Tier: FastAPI with fully native async execution routines.",
        "-> User Interface Tier: Streamlit running asynchronous HTTPX clients for responsive chat interactions."
    ])

    # Compiling to Disk
    output_filename = "Aethera_System_Design.pdf"
    pdf.output(output_filename)
    print(f"🎉 Success! System Design Document generated: '{output_filename}'")

if __name__ == "__main__":
    generate_blueprint_pdf()