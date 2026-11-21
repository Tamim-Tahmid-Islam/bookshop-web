#!/usr/bin/env python3
"""
Populates PageVault with 100 world-renowned books across 12 diverse genres.
Generates tailored, high-resolution SVG book covers for every book.
Ensures exactly 3 books have stock <= 20 for the Urgent Inventory Alert system.
"""

import os
import sqlite3
import html
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COVERS_DIR = os.path.join(BASE_DIR, 'static', 'img', 'covers')
os.makedirs(COVERS_DIR, exist_ok=True)

# Palette definitions by category id
CATEGORY_PALETTES = {
    1: {'bg1': '#0F172A', 'bg2': '#1E293B', 'accent': '#38BDF8', 'accent2': '#0284C7', 'name': 'DATABASE & SYSTEMS'},
    2: {'bg1': '#064E3B', 'bg2': '#022C22', 'accent': '#34D399', 'accent2': '#10B981', 'name': 'COMPUTER SCIENCE'},
    3: {'bg1': '#111827', 'bg2': '#1F2937', 'accent': '#818CF8', 'accent2': '#6366F1', 'name': 'ARTIFICIAL INTELLIGENCE'},
    4: {'bg1': '#3B0764', 'bg2': '#2E1065', 'accent': '#FBBF24', 'accent2': '#F59E0B', 'name': 'FANTASY & ADVENTURE'},
    5: {'bg1': '#09090B', 'bg2': '#18181B', 'accent': '#06B6D4', 'accent2': '#0891B2', 'name': 'SCIENCE FICTION'},
    6: {'bg1': '#1C1917', 'bg2': '#292524', 'accent': '#FB923C', 'accent2': '#EA580C', 'name': 'SELF-HELP & GROWTH'},
    7: {'bg1': '#022C22', 'bg2': '#064E3B', 'accent': '#FDE047', 'accent2': '#CA8A04', 'name': 'FINANCE & ECONOMICS'},
    8: {'bg1': '#4C0519', 'bg2': '#3F0414', 'accent': '#FDE68A', 'accent2': '#D97706', 'name': 'CLASSIC DRAMA'},
    9: {'bg1': '#1E1B4B', 'bg2': '#171337', 'accent': '#F472B6', 'accent2': '#EC4899', 'name': 'INSPIRATIONAL FICTION'},
    10: {'bg1': '#18181B', 'bg2': '#09090B', 'accent': '#EF4444', 'accent2': '#B91C1C', 'name': 'THRILLER & MYSTERY'},
    11: {'bg1': '#451A03', 'bg2': '#321404', 'accent': '#FDE68A', 'accent2': '#D97706', 'name': 'HISTORY & BIOGRAPHY'},
    12: {'bg1': '#2E1065', 'bg2': '#1E1B4B', 'accent': '#FED7AA', 'accent2': '#FB923C', 'name': 'CONTEMPORARY FICTION'}
}

def generate_svg_cover(book_id, title, subtitle, author, cat_id, year):
    pal = CATEGORY_PALETTES.get(cat_id, CATEGORY_PALETTES[1])
    cat_label = pal['name']
    
    # Split title into lines
    words = title.split()
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(' '.join(curr)) > 16:
            lines.append(' '.join(curr))
            curr = []
    if curr:
        lines.append(' '.join(curr))
    lines = lines[:3]

    tspan_html = ""
    y_start = 175 if len(lines) == 1 else (155 if len(lines) == 2 else 135)
    for i, line in enumerate(lines):
        esc_line = html.escape(line)
        dy = 0 if i == 0 else 38
        tspan_html += f'<tspan x="55" dy="{dy}">{esc_line}</tspan>'

    esc_sub = html.escape(subtitle[:40] if subtitle else '')
    esc_author = html.escape(author)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_{book_id}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{pal['bg1']}"/>
      <stop offset="100%" stop-color="{pal['bg2']}"/>
    </linearGradient>
    <linearGradient id="acc_{book_id}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{pal['accent']}"/>
      <stop offset="100%" stop-color="{pal['accent2']}"/>
    </linearGradient>
  </defs>
  <!-- Background -->
  <rect width="400" height="600" fill="url(#bg_{book_id})" rx="8"/>
  <!-- Border -->
  <rect x="18" y="18" width="364" height="564" fill="none" stroke="url(#acc_{book_id})" stroke-width="1.8" rx="4" opacity="0.65"/>
  <rect x="24" y="24" width="352" height="552" fill="none" stroke="url(#acc_{book_id})" stroke-width="0.8" rx="3" opacity="0.25"/>
  <!-- Spine Depth -->
  <line x1="36" y1="18" x2="36" y2="582" stroke="rgba(255,255,255,0.08)" stroke-width="3"/>
  <line x1="39" y1="18" x2="39" y2="582" stroke="rgba(0,0,0,0.35)" stroke-width="1.5"/>
  <!-- Category Badge -->
  <rect x="55" y="46" width="160" height="24" rx="4" fill="rgba(255,255,255,0.08)"/>
  <text x="135" y="62" fill="{pal['accent']}" font-family="'Segoe UI', sans-serif" font-size="10.5" font-weight="700" letter-spacing="1.2" text-anchor="middle">{cat_label}</text>
  <!-- Book Title -->
  <text x="55" y="{y_start}" fill="#FFFFFF" font-family="'Cinzel', Georgia, serif" font-size="28" font-weight="700">
    {tspan_html}
  </text>
  <!-- Subtitle -->
  {f'<text x="55" y="{y_start + len(lines)*38 + 14}" fill="#94A3B8" font-family="\'Segoe UI\', sans-serif" font-size="13" font-weight="500">{esc_sub}</text>' if esc_sub else ''}
  <!-- Ornament divider -->
  <g transform="translate(55, 340)">
    <line x1="0" y1="0" x2="110" y2="0" stroke="url(#acc_{book_id})" stroke-width="1.5" opacity="0.7"/>
    <circle cx="125" cy="0" r="4" fill="{pal['accent']}"/>
    <line x1="140" y1="0" x2="250" y2="0" stroke="url(#acc_{book_id})" stroke-width="1.5" opacity="0.7"/>
  </g>
  <!-- Author Section -->
  <text x="55" y="475" fill="{pal['accent']}" font-family="'Segoe UI', sans-serif" font-size="11" font-weight="700" letter-spacing="1.5">AUTHOR</text>
  <text x="55" y="504" fill="#FFFFFF" font-family="'Cinzel', Georgia, serif" font-size="19" font-weight="700">{esc_author}</text>
  <!-- Imprint -->
  <text x="345" y="552" fill="#64748B" font-family="'Segoe UI', sans-serif" font-size="10" font-weight="700" text-anchor="end">PAGEVAULT &bull; {year}</text>
</svg>'''

# 12 Categories
CATEGORIES = [
    (1, 'Database & Systems', 'database-systems', 'Relational models, SQL optimization, index structures and distributed databases.', 'database'),
    (2, 'Computer Science & Software', 'computer-science', 'Algorithms, system design, clean architecture, and computing principles.', 'cpu'),
    (3, 'Artificial Intelligence', 'artificial-intelligence', 'Machine learning, neural networks, intelligent agents, and reasoning.', 'brain'),
    (4, 'Fantasy & Adventure', 'fantasy-adventure', 'Magical universes, epic sagas, heroic quests, and legendary chronicles.', 'sparkles'),
    (5, 'Science Fiction & Dystopia', 'science-fiction', 'Futuristic speculative universes, political dystopias, and space operas.', 'rocket'),
    (6, 'Self-Help & Personal Growth', 'self-help', 'Productivity, habit engineering, mental toughness, and behavioral psychology.', 'zap'),
    (7, 'Finance & Behavioral Economics', 'finance-economics', 'Wealth building, rational decision making, and cognitive bias analysis.', 'trending-up'),
    (8, 'Classic Drama & Poetry', 'classic-drama', 'Timeless theatrical tragedies, comedies, historical plays, and verse.', 'book-open'),
    (9, 'Inspirational Fiction', 'inspirational-fiction', 'Philosophical allegories, spiritual voyages, and transformative tales.', 'compass'),
    (10, 'Thriller, Mystery & Crime', 'thriller-mystery', 'Grips, detective investigations, psychological suspense, and conspiracies.', 'shield-alert'),
    (11, 'History & Biography', 'history-biography', 'Human civilizations, scientific revolutions, and transformative memoirs.', 'globe'),
    (12, 'Contemporary Fiction', 'contemporary-fiction', 'Modern emotional journeys, human relationships, and celebrated fiction.', 'feather')
]

# 16 Publishers
PUBLISHERS = [
    (1, 'Addison-Wesley Professional', 'USA', 1942, 'https://www.pearson.com'),
    (2, 'O\'Reilly Media', 'USA', 1978, 'https://www.oreilly.com'),
    (3, 'The MIT Press', 'USA', 1962, 'https://mitpress.mit.edu'),
    (4, 'Morgan Kaufmann', 'USA', 1984, 'https://www.elsevier.com'),
    (5, 'Penguin Random House', 'USA', 1927, 'https://www.penguinrandomhouse.com'),
    (6, 'HarperCollins Publishers', 'USA', 1817, 'https://www.harpercollins.com'),
    (7, 'Bloomsbury Publishing', 'UK', 1986, 'https://www.bloomsbury.com'),
    (8, 'Scholastic Inc.', 'USA', 1920, 'https://www.scholastic.com'),
    (9, 'Simon & Schuster', 'USA', 1924, 'https://www.simonandschuster.com'),
    (10, 'Avery Publishing', 'USA', 1976, 'https://www.penguin.com'),
    (11, 'Harriman House', 'UK', 1992, 'https://harriman-house.com'),
    (12, 'Tor Books', 'USA', 1980, 'https://torforgeblog.com'),
    (13, 'Vintage Books', 'USA', 1954, 'https://www.penguin.co.uk'),
    (14, 'Oxford University Press', 'UK', 1586, 'https://global.oup.com'),
    (15, 'Pragmatic Bookshelf', 'USA', 2003, 'https://pragprog.com'),
    (16, 'Grand Central Publishing', 'USA', 1970, 'https://www.hachettebookgroup.com')
]

# 60 Authors
AUTHORS = [
    (1, 'Abraham Silberschatz', 'Professor of Computer Science at Yale University; renowned author of database textbooks.', 1947, 'USA'),
    (2, 'Martin Kleppmann', 'Researcher in distributed systems at University of Cambridge; author of DDIA.', 1982, 'UK'),
    (3, 'C.J. Date', 'Independent author specializing in relational database theory and SQL foundation.', 1938, 'UK'),
    (4, 'Robert C. Martin', 'Co-author of Agile Manifesto, known as Uncle Bob.', 1952, 'USA'),
    (5, 'Thomas H. Cormen', 'Emeritus Professor of Computer Science at Dartmouth College; co-author of CLRS.', 1956, 'USA'),
    (6, 'Donald E. Knuth', 'Professor Emeritus at Stanford University; father of algorithm analysis.', 1938, 'USA'),
    (7, 'Martin Fowler', 'Chief Scientist at ThoughtWorks; authority on refactoring and software architecture.', 1963, 'UK'),
    (8, 'Stuart Russell', 'Professor of Computer Science at UC Berkeley; AI pioneer.', 1962, 'UK'),
    (9, 'Peter Norvig', 'Director of Research at Google; computer scientist and educator.', 1956, 'USA'),
    (10, 'Frank Herbert', 'American science fiction author best known for the epic Dune saga.', 1920, 'USA'),
    (11, 'George Orwell', 'English novelist, essayist, and critic known for 1984 and Animal Farm.', 1903, 'UK'),
    (12, 'James Clear', 'Renowned researcher on habits, decision making, and author of Atomic Habits.', 1986, 'USA'),
    (13, 'Morgan Housel', 'Partner at Collaborative Fund and bestselling author on behavioral finance.', 1984, 'USA'),
    (14, 'Daniel Kahneman', 'Nobel laureate in Economics and pioneer of behavioral psychology.', 1934, 'Israel'),
    (15, 'William Shakespeare', 'Legendary English playwright, poet, and dramatist.', 1564, 'UK'),
    (16, 'Paulo Coelho', 'Acclaimed Brazilian novelist whose allegories have sold over 320M copies.', 1947, 'Brazil'),
    (17, 'J.K. Rowling', 'British author celebrated worldwide for creating the Harry Potter universe.', 1965, 'UK'),
    (18, 'J.R.R. Tolkien', 'Oxford philologist and creator of Middle-earth, author of The Lord of the Rings.', 1892, 'UK'),
    (19, 'Arthur Conan Doyle', 'Creator of legendary consulting detective Sherlock Holmes.', 1859, 'UK'),
    (20, 'Agatha Christie', 'The Queen of Crime and best-selling fiction writer of all time.', 1890, 'UK'),
    (21, 'Dan Brown', 'Master of symbology thrillers and author of The Da Vinci Code.', 1964, 'USA'),
    (22, 'Gillian Flynn', 'Bestselling author of psychological thrillers including Gone Girl.', 1971, 'USA'),
    (23, 'Alex Michaelides', 'British-Cypriot author and screenwriter; author of The Silent Patient.', 1977, 'Cyprus'),
    (24, 'Dennis Lehane', 'Author of acclaimed dark psychological thrillers including Shutter Island.', 1965, 'USA'),
    (25, 'Stieg Larsson', 'Swedish author and journalist; creator of the Millennium series.', 1954, 'Sweden'),
    (26, 'Yuval Noah Harari', 'Historian, philosopher, and author of Sapiens and Homo Deus.', 1976, 'Israel'),
    (27, 'Jared Diamond', 'Geographer, historian, and Pulitzer Prize-winning author.', 1937, 'USA'),
    (28, 'Bill Bryson', 'Celebrated non-fiction author known for witty science and travel chronicles.', 1951, 'USA'),
    (29, 'Walter Isaacson', 'Historian and biographer of Steve Jobs, Einstein, and Da Vinci.', 1952, 'USA'),
    (30, 'Michelle Obama', 'Lawyer, author, and Former First Lady of the United States.', 1964, 'USA'),
    (31, 'Khaled Hosseini', 'Afghan-American novelist; author of The Kite Runner.', 1965, 'Afghanistan'),
    (32, 'Yann Martel', 'Canadian author best known for the Man Booker Prize-winning Life of Pi.', 1963, 'Canada'),
    (33, 'Markus Zusak', 'Australian author internationally acclaimed for The Book Thief.', 1975, 'Australia'),
    (34, 'Aldous Huxley', 'English writer and philosopher; author of Brave New World.', 1894, 'UK'),
    (35, 'Ray Bradbury', 'American master of speculative fiction; author of Fahrenheit 451.', 1920, 'USA'),
    (36, 'Douglas Adams', 'English author and satirist; creator of Hitchhiker’s Guide.', 1952, 'UK'),
    (37, 'William Gibson', 'Pioneering sci-fi novelist who coined the term cyberspace.', 1948, 'USA'),
    (38, 'Isaac Asimov', 'Legendary polymath and author of the Foundation and Robot series.', 1920, 'USA'),
    (39, 'Andy Weir', 'Software engineer turned bestselling sci-fi author of The Martian.', 1972, 'USA'),
    (40, 'Cixin Liu', 'Leading Chinese science fiction writer; author of The Three-Body Problem.', 1963, 'China'),
    (41, 'Mark Manson', 'Self-help author and blogger known for pragmatic, no-BS approaches.', 1984, 'USA'),
    (42, 'Cal Newport', 'Associate Professor of Computer Science at Georgetown University.', 1982, 'USA'),
    (43, 'David Goggins', 'Retired Navy SEAL and ultramarathon runner.', 1975, 'USA'),
    (44, 'Stephen R. Covey', 'Keynote speaker and leadership authority; author of 7 Habits.', 1932, 'USA'),
    (45, 'Dale Carnegie', 'Pioneer in public speaking, leadership, and interpersonal communication.', 1888, 'USA'),
    (46, 'Carol S. Dweck', 'Lewis and Virginia Eaton Professor of Psychology at Stanford.', 1946, 'USA'),
    (47, 'Robert T. Kiyosaki', 'Businessman, investor, and educator; author of Rich Dad Poor Dad.', 1947, 'USA'),
    (48, 'Benjamin Graham', 'Father of value investing and mentor to Warren Buffett.', 1894, 'UK'),
    (49, 'Ray Dalio', 'Founder of Bridgewater Associates, the world’s largest hedge fund.', 1949, 'USA'),
    (50, 'F. Scott Fitzgerald', 'Iconic author of Jazz Age literature and The Great Gatsby.', 1896, 'USA'),
    (51, 'Harper Lee', 'Pulitzer Prize-winning author of To Kill a Mockingbird.', 1926, 'USA'),
    (52, 'Fyodor Dostoevsky', 'Russian literary master of existentialism and psychological drama.', 1821, 'Russia'),
    (53, 'Jane Austen', 'English novelist celebrated for her social realism and wit.', 1775, 'UK'),
    (54, 'Charlotte Brontë', 'English novelist and poet; author of Jane Eyre.', 1816, 'UK'),
    (55, 'Antoine de Saint-Exupéry', 'French writer, poet, and aviator; creator of The Little Prince.', 1900, 'France'),
    (56, 'Hermann Hesse', 'Nobel laureate German-Swiss poet and novelist; author of Siddhartha.', 1877, 'Germany'),
    (57, 'Kahlil Gibran', 'Lebanese-American philosophical poet and artist; author of The Prophet.', 1883, 'Lebanon'),
    (58, 'Mitch Albom', 'Author, journalist, and philanthropist; author of Tuesdays with Morrie.', 1958, 'USA'),
    (59, 'Ian Goodfellow', 'AI researcher; pioneer of Generative Adversarial Networks (GANs).', 1985, 'USA'),
    (60, 'Aurélien Géron', 'Machine learning consultant and former lead of YouTube video classification.', 1978, 'France')
]

# 100 Books
# Format: (book_id, isbn, title, subtitle, pub_id, cat_id, price, discount_pct, stock_qty, year, pages, primary_author_id, description)
# Exactly 3 books have stock <= 20:
# Book 10: stock = 18 (CLRS)
# Book 11: stock = 8 (The Art of Computer Programming)
# Book 12: stock = 14 (Design Patterns GoF)
# All other 97 books have stock between 35 and 150.
BOOKS = [
    # 1-8: Database & Systems
    (1, '978-0078022159', 'Database System Concepts', 'Seventh Edition', 4, 1, 1250.00, 10.0, 45, 2019, 1376, 1,
     'The definitive foundation textbook covering relational database architectures, SQL optimization, index models, transaction management, and concurrency control.'),
    (2, '978-1449373320', 'Designing Data-Intensive Applications', 'The Big Ideas Behind Reliable Systems', 2, 1, 950.00, 15.0, 60, 2017, 616, 2,
     'An indispensable masterwork on database storage engines, replication, partitioning, consensus, stream processing, and distributed reliability.'),
    (3, '978-0321392794', 'An Introduction to Database Systems', 'Eighth Edition', 1, 1, 1100.00, 10.0, 42, 2003, 1024, 3,
     'C.J. Date’s monumental theoretical work on the relational model, relational algebra, tuple calculus, normalization, and ACID integrity.'),
    (4, '978-1492080510', 'High Performance MySQL', 'Optimization, Backups, and Replication', 2, 1, 850.00, 5.0, 38, 2021, 380, 2,
     'Practical strategies for tuning MySQL query execution, indexing architectures, replica topology, and cloud database performance.'),
    (5, '978-1492040347', 'Database Internals', 'A Deep Dive into How Distributed Systems Work', 2, 1, 920.00, 10.0, 48, 2019, 372, 2,
     'Examines the internal mechanics of storage engines, B-tree variants, LSM trees, consensus algorithms, and distributed transaction protocols.'),
    (6, '978-1491977019', 'Streaming Systems', 'The What, Where, When, and How of Large-Scale Data', 2, 1, 890.00, 10.0, 52, 2018, 334, 2,
     'Comprehensive architectural blueprint for modern stream processing, event-time semantics, watermarks, and stateful stream joins.'),
    (7, '978-1934356555', 'SQL Antipatterns', 'Avoiding the Pitfalls of Database Programming', 15, 1, 650.00, 0.0, 40, 2010, 328, 3,
     'Identifies common mistakes software engineers make when designing relational database tables, queries, and architectural models.'),
    (8, '978-1680502534', 'Seven Databases in Seven Weeks', 'A Guide to Modern Databases', 15, 1, 780.00, 10.0, 36, 2018, 350, 1,
     'Hands-on exploration of relational, document, key-value, column-family, and graph databases including PostgreSQL, Redis, Neo4j, and MongoDB.'),

    # 9-18: Computer Science & Software Engineering
    (9, '978-0134494166', 'Clean Architecture', 'A Craftsman\'s Guide to Software Structure', 1, 2, 650.00, 5.0, 55, 2017, 432, 4,
     'Universal rules of software architecture: separation of concerns, domain boundaries, dependency inversion, and component coupling.'),
    (10, '978-0262033848', 'Introduction to Algorithms (CLRS)', 'Fourth Edition', 3, 2, 1450.00, 12.0, 18, 2022, 1312, 5,
     'The definitive international standard textbook on computer algorithms, data structures, dynamic programming, and complexity analysis.'),
    (11, '978-0321751041', 'The Art of Computer Programming, Vol 1', 'Fundamental Algorithms', 1, 2, 1350.00, 0.0, 8, 1997, 672, 6,
     'Donald Knuth’s magnum opus on mathematical algorithm analysis, discrete data structures, memory representations, and fundamental algorithms.'),
    (12, '978-0201633610', 'Design Patterns: Elements of Reusable Software', 'Classic Gang of Four Edition', 1, 2, 750.00, 15.0, 14, 1994, 416, 7,
     'The timeless catalog of 23 software design patterns categorized into Creational, Structural, and Behavioral solutions.'),
    (13, '978-0321127426', 'Patterns of Enterprise Application Architecture', 'Data Mapping and Domain Models', 1, 2, 850.00, 5.0, 35, 2002, 560, 7,
     'Industry-standard architectural patterns for enterprise software, object-relational mapping, unit of work, and domain logic layers.'),
    (14, '978-0132350884', 'Clean Code', 'A Handbook of Agile Software Craftsmanship', 1, 2, 680.00, 10.0, 65, 2008, 464, 4,
     'Revolutionary principles for writing readable, maintainable, self-documenting code with rigorous unit testing and clean formatting.'),
    (15, '978-0135957059', 'The Pragmatic Programmer', '20th Anniversary Edition', 1, 2, 720.00, 10.0, 50, 2019, 352, 7,
     'Timeless practical advice for software engineers covering career mastery, continuous learning, debugging, and code responsibility.'),
    (16, '978-0134757599', 'Refactoring', 'Improving the Design of Existing Code', 1, 2, 790.00, 8.0, 42, 2018, 448, 7,
     'The quintessential guide to identifying code smells and systematically restructuring software without altering observable external behavior.'),
    (17, '978-0262510875', 'Structure and Interpretation of Computer Programs', 'Second Edition (SICP)', 3, 2, 980.00, 0.0, 35, 1996, 657, 5,
     'The legendary MIT computer science curriculum text on abstraction, computational processes, recursion, and interpreter construction.'),
    (18, '978-0735619678', 'Code Complete', 'A Practical Handbook of Software Construction', 1, 2, 920.00, 10.0, 38, 2004, 960, 4,
     'Comprehensive manual of software construction best practices, defensive programming, variable naming, and collaborative engineering.'),

    # 19-26: Artificial Intelligence & Data
    (19, '978-0134610993', 'Artificial Intelligence: A Modern Approach', 'Fourth Edition', 1, 3, 1600.00, 8.0, 45, 2020, 1168, 8,
     'The world standard introductory textbook on AI: intelligent agents, search algorithms, logic reasoning, probabilistic models, and neural nets.'),
    (20, '978-0262035613', 'Deep Learning', 'Adaptive Computation and Machine Learning', 3, 3, 1350.00, 10.0, 50, 2016, 800, 59,
     'Ian Goodfellow and Yoshua Bengio’s seminal text on deep feedforward networks, convolution, sequence modeling, and representation learning.'),
    (21, '978-0387310732', 'Pattern Recognition and Machine Learning', 'Information Science and Statistics', 14, 3, 1250.00, 5.0, 40, 2006, 738, 8,
     'Christopher Bishop’s classic Bayesian formulation of machine learning, linear models, kernels, graphical models, and sampling.'),
    (22, '978-1098125974', 'Hands-On Machine Learning', 'With Scikit-Learn, Keras, and TensorFlow', 2, 3, 1150.00, 12.0, 55, 2022, 856, 60,
     'Practical, project-driven guide to training modern ML pipelines, deep neural networks, transformers, and computer vision models.'),
    (23, '978-1999579517', 'The Hundred-Page Machine Learning Book', 'Core Concepts Explained', 15, 3, 550.00, 0.0, 48, 2019, 160, 60,
     'Concise yet rigorous overview of supervised, unsupervised, and semi-supervised machine learning algorithms by Andriy Burkov.'),
    (24, '978-0262039246', 'Reinforcement Learning: An Introduction', 'Second Edition', 3, 3, 1100.00, 10.0, 38, 2018, 552, 8,
     'Sutton and Barto’s authoritative guide to Markov decision processes, dynamic programming, temporal-difference learning, and policy gradients.'),
    (25, '978-0198739838', 'Superintelligence', 'Paths, Dangers, Strategies', 14, 3, 620.00, 10.0, 44, 2014, 352, 8,
     'Nick Bostrom’s influential philosophical examination of the existential risks, alignment problem, and control mechanisms for AGI.'),
    (26, '978-1101946596', 'Life 3.0', 'Being Human in the Age of Artificial Intelligence', 5, 3, 580.00, 10.0, 48, 2017, 384, 8,
     'Physicist Max Tegmark explores how artificial intelligence will shape employment, warfare, consciousness, and the cosmic future of life.'),

    # 27-36: Fantasy & Adventure
    (27, '978-0590353427', 'Harry Potter and the Sorcerer\'s Stone', 'Book 1 of Hogwarts Series', 8, 4, 620.00, 10.0, 95, 1997, 309, 17,
     'Harry Potter discovers he is a wizard destined for Hogwarts School of Witchcraft and Wizardry, embarking on an extraordinary journey.'),
    (28, '978-0439064873', 'Harry Potter and the Chamber of Secrets', 'Book 2 of Hogwarts Series', 8, 4, 650.00, 10.0, 85, 1998, 341, 17,
     'Dark whispers echo through Hogwarts castle as students are petrified and the long-sealed Chamber of Secrets is opened anew.'),
    (29, '978-0439136365', 'Harry Potter and the Prisoner of Azkaban', 'Book 3 of Hogwarts Series', 8, 4, 680.00, 12.0, 90, 1999, 435, 17,
     'Dementors patrol Hogwarts looking for escaped fortress prisoner Sirius Black, forcing Harry to confront secrets of his past.'),
    (30, '978-0439139601', 'Harry Potter and the Goblet of Fire', 'Book 4 of Hogwarts Series', 8, 4, 750.00, 15.0, 75, 2000, 734, 17,
     'The Triwizard Tournament arrives at Hogwarts, plunging Harry into dangerous trials culminating in the return of Lord Voldemort.'),
    (31, '978-0439358071', 'Harry Potter and the Order of the Phoenix', 'Book 5 of Hogwarts Series', 8, 4, 780.00, 10.0, 80, 2003, 870, 17,
     'Harry and his allies form Dumbledore\'s Army to prepare for open warfare against Voldemort while navigating Ministry denial.'),
    (32, '978-0439785969', 'Harry Potter and the Half-Blood Prince', 'Book 6 of Hogwarts Series', 8, 4, 790.00, 10.0, 85, 2005, 652, 17,
     'Dumbledore guides Harry through Voldemort\'s past memories to discover the secret Horcruxes holding the Dark Lord\'s soul.'),
    (33, '978-0545010221', 'Harry Potter and the Deathly Hallows', 'Book 7: The Final Battle', 8, 4, 820.00, 15.0, 90, 2007, 759, 17,
     'The climatic finale: Harry, Ron, and Hermione hunt down Horcruxes to destroy Lord Voldemort once and for all at the Battle of Hogwarts.'),
    (34, '978-0547928227', 'The Hobbit', 'There and Back Again', 6, 4, 520.00, 10.0, 70, 1937, 310, 18,
     'Bilbo Baggins is swept into an epic quest by Gandalf and thirteen dwarves to reclaim the lonely mountain and its treasure from Smaug.'),
    (35, '978-0544003415', 'The Fellowship of the Ring', 'Part One of The Lord of the Rings', 6, 4, 680.00, 10.0, 75, 1954, 432, 18,
     'Frodo Baggins inherits the One Ring of Sauron and sets forth across Middle-earth accompanied by an alliance of men, elves, and dwarves.'),
    (36, '978-0756404741', 'The Name of the Wind', 'The Kingkiller Chronicle: Day One', 12, 4, 640.00, 5.0, 55, 2007, 662, 18,
     'Patrick Rothfuss\'s lyrical tale of Kvothe, an orphaned prodigy who grows into the most notorious wizard the world has ever known.'),

    # 37-46: Science Fiction & Dystopia
    (37, '978-0441013593', 'Dune', 'The Epic Science Fiction Masterpiece', 5, 5, 550.00, 20.0, 110, 1965, 896, 10,
     'Set on the desert planet Arrakis, Dune is the story of young Paul Atreides who inherits a cosmic planetary destiny amidst intergalactic strife.'),
    (38, '978-0451524935', '1984', 'A Dystopian Classic', 5, 5, 350.00, 0.0, 85, 1949, 328, 11,
     'Winston Smith rebels against totalitarian surveillance, doublethink, and the omnipresent reign of Big Brother in London of 1984.'),
    (39, '978-0060850524', 'Brave New World', 'Classic Dystopian Satire', 6, 5, 380.00, 5.0, 65, 1932, 288, 34,
     'Aldous Huxley\'s chilling vision of an engineered consumer society dominated by biological conditioning and state-mandated pacification.'),
    (40, '978-1451673319', 'Fahrenheit 451', 'The Temperature at Which Book Paper Burns', 9, 5, 360.00, 10.0, 70, 1953, 249, 35,
     'Guy Montag is a fireman whose job is to burn forbidden books, until he meets an enigmatic girl who challenges his view of conformity.'),
    (41, '978-0345391803', 'The Hitchhiker\'s Guide to the Galaxy', 'A Trilogy in Five Parts', 13, 5, 420.00, 10.0, 60, 1979, 216, 36,
     'Seconds before Earth is demolished to make way for a galactic bypass, Arthur Dent is plucked into space by his alien friend Ford Prefect.'),
    (42, '978-0441569595', 'Neuromancer', 'Sprawl Trilogy: Book 1', 5, 5, 450.00, 0.0, 55, 1984, 271, 37,
     'William Gibson\'s groundbreaking cyberpunk masterpiece: washed-up data thief Case is recruited for an ultimate high-stakes cyberspace hack.'),
    (43, '978-0553293357', 'Foundation', 'The Foundation Series: Book 1', 5, 5, 480.00, 10.0, 65, 1951, 255, 38,
     'Hari Seldon invents psychohistory to predict the inevitable fall of the Galactic Empire, creating the Foundation to preserve human knowledge.'),
    (44, '978-0812550702', 'Ender\'s Game', 'The Ender Quintet: Book 1', 12, 5, 490.00, 10.0, 70, 1985, 324, 38,
     'Child genius Ender Wiggin is sent to an orbital military academy to prepare for an impending invasion by an alien insectoid species.'),
    (45, '978-0593135204', 'Project Hail Mary', 'A Novel of Cosmic Survival', 5, 5, 620.00, 12.0, 80, 2021, 496, 39,
     'Ryland Grace awakens alone with amnesia on a starship lightyears from Earth, tasked with solving an extinction-level solar parasite threat.'),
    (46, '978-0765382030', 'The Three-Body Problem', 'Remembrance of Earth\'s Past: Book 1', 12, 5, 590.00, 10.0, 75, 2008, 400, 40,
     'Cixin Liu\'s sprawling hard sci-fi epic: humanity sends a signal into deep space, triggering an alien fleet on a centuries-long voyage to Earth.'),

    # 47-56: Self-Help & Personal Growth
    (47, '978-0735211292', 'Atomic Habits', 'Tiny Changes, Remarkable Results', 10, 6, 550.00, 15.0, 140, 2018, 320, 12,
     'James Clear reveals practical, neuroscience-backed frameworks for building good habits, breaking bad ones, and mastering tiny behaviors.'),
    (48, '978-0062457714', 'The Subtle Art of Not Giving a F*ck', 'A Counterintuitive Approach to Living a Good Life', 6, 6, 480.00, 10.0, 115, 2016, 224, 41,
     'Mark Manson cuts through modern toxic positivity to teach pragmatic resilience, honest self-awareness, and choosing meaningful values.'),
    (49, '978-1455586691', 'Deep Work', 'Rules for Focused Success in a Distracted World', 16, 6, 520.00, 10.0, 85, 2016, 304, 42,
     'Cal Newport demonstrates how cultivating distraction-free focus enables individuals to master complex topics and produce superior output.'),
    (50, '978-1544512280', 'Can\'t Hurt Me', 'Master Your Mind and Defy the Odds', 16, 6, 590.00, 12.0, 90, 2018, 364, 43,
     'Navy SEAL David Goggins shares his philosophy of mental discipline, overcoming adversity, and reaching peak potential through the 40% rule.'),
    (51, '978-1982137274', 'The 7 Habits of Highly Effective People', 'Powerful Lessons in Personal Change', 9, 6, 540.00, 10.0, 95, 1989, 432, 44,
     'Stephen R. Covey\'s holistic, principle-centered approach for solving personal and professional problems through character ethics.'),
    (52, '978-0671027032', 'How to Win Friends and Influence People', 'The Only Book You Need to Lead You to Success', 9, 6, 420.00, 10.0, 100, 1936, 288, 45,
     'Dale Carnegie’s timeless masterpiece on effective interpersonal communication, genuine praise, winning people over, and leading without friction.'),
    (53, '978-0345472328', 'Mindset: The New Psychology of Success', 'How We Can Learn to Fulfill Our Potential', 5, 6, 490.00, 5.0, 80, 2006, 320, 46,
     'Carol Dweck explains the profound power of growth mindset versus fixed mindset in school, athletics, business, and personal relationships.'),
    (54, '978-0804137386', 'Essentialism', 'The Disciplined Pursuit of Less', 10, 6, 480.00, 10.0, 75, 2014, 272, 42,
     'Greg McKeown shows how discerning what is absolutely vital allows high achievers to channel maximum energy and make their highest contribution.'),
    (55, '978-1591847816', 'Ego Is the Enemy', 'The Fight to Master Our Greatest Opponent', 10, 6, 450.00, 10.0, 65, 2016, 256, 41,
     'Ryan Holiday draws on Stoic philosophy and historical case studies to illustrate how ego undermines ambition, success, and resilience.'),
    (56, '978-1455570249', 'Make Your Bed', 'Little Things That Can Change Your Life...And Maybe the World', 16, 6, 380.00, 0.0, 70, 2017, 130, 43,
     'Admiral William H. McRaven shares 10 life-changing principles forged in Navy SEAL training to overcome dark times and achieve daily greatness.'),

    # 57-64: Finance & Behavioral Economics
    (57, '978-0857197689', 'The Psychology of Money', 'Timeless Lessons on Wealth, Greed, and Happiness', 11, 7, 540.00, 10.0, 130, 2020, 252, 13,
     'Morgan Housel explores 19 short stories demonstrating that financial success is less about spreadsheet math and more about behavioral control.'),
    (58, '978-0374533557', 'Thinking, Fast and Slow', 'Cognitive Biases and Decision Systems', 5, 7, 580.00, 10.0, 64, 2011, 512, 14,
     'Nobel laureate Daniel Kahneman reveals the dual cognitive systems shaping judgments: fast, intuitive System 1 versus deliberative System 2.'),
    (59, '978-1612680194', 'Rich Dad Poor Dad', 'What the Rich Teach Their Kids About Money', 11, 7, 460.00, 10.0, 120, 1997, 336, 47,
     'Robert Kiyosaki challenges the myth that high income is required to be rich, explaining asset acquisition, cash flow, and financial literacy.'),
    (60, '978-0060555665', 'The Intelligent Investor', 'The Definitive Book on Value Investing', 6, 7, 720.00, 15.0, 65, 1949, 640, 48,
     'Benjamin Graham’s foundational text on value investing, margin of safety, and safeguarding capital against emotional market turbulence.'),
    (61, '978-0143115762', 'Your Money or Your Life', '9 Steps to Transforming Your Relationship with Money', 5, 7, 480.00, 5.0, 50, 1992, 368, 13,
     'Vicki Robin presents a transformative roadmap for achieving financial independence and aligning consumption with genuine life energy.'),
    (62, '978-1501124020', 'Principles: Life and Work', 'Actionable Rules for Decisions and Management', 9, 7, 750.00, 10.0, 55, 2017, 592, 49,
     'Billionaire investor Ray Dalio shares the unconventional management and decision-making principles that built Bridgewater Associates.'),
    (63, '978-0060731335', 'Freakonomics', 'A Rogue Economist Explores the Hidden Side of Everything', 6, 7, 490.00, 10.0, 70, 2005, 336, 14,
     'Steven Levitt and Stephen Dubner examine how incentives govern human behavior, uncovering surprising economic truths behind everyday life.'),
    (64, '978-1589795471', 'The Millionaire Next Door', 'The Surprising Secrets of America\'s Wealthy', 11, 7, 480.00, 5.0, 60, 1996, 272, 47,
     'Thomas Stanley uncovers the unglamorous reality of wealth building: frugality, living below one\'s means, and steady capital compounding.'),

    # 65-74: Classic Literature & Drama
    (65, '978-0743477123', 'Hamlet, Prince of Denmark', 'The Folger Shakespeare Library', 9, 8, 320.00, 0.0, 90, 1603, 342, 15,
     'Prince Hamlet mourns his murdered father, facing moral paralysis, revenge, feigned madness, and profound existential questions in Elsinore.'),
    (66, '978-0743477109', 'Macbeth', 'Tragedy of Ambition and Fate', 9, 8, 300.00, 0.0, 85, 1606, 240, 15,
     'Spurred by supernatural witches and Lady Macbeth, general Macbeth commits regicide to seize the crown, descending into paranoid tyranny.'),
    (67, '978-0743477116', 'Romeo and Juliet', 'The Definitive Folger Edition', 9, 8, 290.00, 0.0, 95, 1597, 281, 15,
     'The timeless drama of star-crossed young lovers in Verona whose romance defies the bitter, violent blood feud between the Montagues and Capulets.'),
    (68, '978-0743273565', 'The Great Gatsby', 'The Authorized Scribner Edition', 9, 8, 380.00, 10.0, 90, 1925, 180, 50,
     'F. Scott Fitzgerald’s lyrical examination of the Roaring Twenties, unrequited love, and the tragic disillusionment of the American Dream.'),
    (69, '978-0141439518', 'Pride and Prejudice', 'Penguin Classics Edition', 5, 8, 360.00, 0.0, 85, 1813, 480, 53,
     'Elizabeth Bennet and the aloof Mr. Darcy navigate societal class, misunderstandings, and family expectations in Regency England.'),
    (70, '978-0060935467', 'To Kill a Mockingbird', '50th Anniversary Edition', 6, 8, 420.00, 10.0, 80, 1960, 336, 51,
     'Atticus Finch defends a wrongly accused Black man in 1930s Alabama, told through the innocent eyes of his young daughter Scout.'),
    (71, '978-0140449136', 'Crime and Punishment', 'Translated by Oliver Ready', 5, 8, 480.00, 10.0, 75, 1866, 672, 52,
     'Impoverished student Raskolnikov tests his theory of superior morality by committing murder, only to face devastating psychological guilt.'),
    (72, '978-0141439570', 'The Picture of Dorian Gray', 'Penguin Classics Deluxe', 5, 8, 350.00, 0.0, 70, 1890, 272, 15,
     'A hedonistic young man sells his soul so his portrait will age while he remains youthful, indulging in moral decadence and aestheticism.'),
    (73, '978-0141441146', 'Jane Eyre', 'Penguin Classics', 5, 8, 370.00, 5.0, 75, 1847, 532, 54,
     'Orphaned Jane Eyre finds work as a governess at mysterious Thornfield Hall, uncovering dark secrets surrounding the brooding Mr. Rochester.'),
    (74, '978-0141439556', 'Wuthering Heights', 'Penguin Classics', 5, 8, 360.00, 0.0, 70, 1847, 416, 54,
     'The tempestuous, destructive passion between Heathcliff and Catherine Earnshaw across the bleak Yorkshire moors across generations.'),

    # 75-82: Inspirational Fiction & Allegory
    (75, '978-0062315007', 'The Alchemist', 'A Fable About Following Your Dream', 6, 9, 380.00, 10.0, 120, 1988, 208, 16,
     'Santiago, an Andalusian shepherd boy, journeys across the desert in search of worldly treasure, discovering his personal legend along the way.'),
    (76, '978-0061578953', 'Brida', 'A Novel of Magic and Mystery', 6, 9, 420.00, 5.0, 65, 1990, 288, 16,
     'The tale of young Brida and her quest for wisdom through ancient spiritual traditions, discovering love and her profound life destiny.'),
    (77, '978-0061735257', 'The Winner Stands Alone', 'Ambition, Fame and the Superclass', 6, 9, 450.00, 10.0, 48, 2008, 400, 16,
     'Set amidst the glamorous backdrop of the Cannes Film Festival, a gripping examination of deep ambition, celebrity culture, and vanity.'),
    (78, '978-0156012195', 'The Little Prince', 'With Original Illustrations', 13, 9, 320.00, 0.0, 95, 1943, 96, 55,
     'A stranded aviator in the Sahara meets a young prince from a distant asteroid who shares poignant wisdom about love and innocence.'),
    (79, '978-0743278904', 'Jonathan Livingston Seagull', 'A Story of Transcendent Flight', 9, 9, 340.00, 5.0, 80, 1970, 112, 16,
     'A seagull is cast out of his flock for refusing to accept that flight is only for scavenging, soaring to higher realms of perfection.'),
    (80, '978-0553208849', 'Siddhartha', 'A Journey to Spiritual Awakening', 13, 9, 350.00, 0.0, 75, 1922, 152, 56,
     'Hermann Hesse’s lyrical account of Siddhartha who abandons comfort in ancient India to seek profound enlightenment and inner peace.'),
    (81, '978-0394404288', 'The Prophet', 'Timeless Words of Wisdom', 13, 9, 360.00, 0.0, 70, 1923, 128, 57,
     'Kahlil Gibran’s 26 philosophical poetic essays on love, marriage, children, giving, work, joy, sorrow, and spiritual freedom.'),
    (82, '978-0767905923', 'Tuesdays with Morrie', 'An Old Man, a Young Man, and Life\'s Greatest Lesson', 13, 9, 410.00, 10.0, 85, 1997, 192, 58,
     'Journalist Mitch Albom reconnects with his dying college mentor Morrie Schwartz for weekly conversations exploring life and acceptance.'),

    # 83-90: Thriller, Mystery & Crime
    (83, '978-0307474278', 'The Da Vinci Code', 'Robert Langdon Series: Book 2', 13, 10, 520.00, 10.0, 95, 2003, 480, 21,
     'Symbologist Robert Langdon investigates an enigmatic murder in the Louvre, discovering clues hidden in Leonardo da Vinci’s paintings.'),
    (84, '978-0743493468', 'Angels & Demons', 'Robert Langdon Series: Book 1', 9, 10, 490.00, 10.0, 85, 2000, 624, 21,
     'Langdon races through Rome and the Vatican to stop a resurgent secret brotherhood from detonating an antimatter device during a conclave.'),
    (85, '978-0307588371', 'Gone Girl', 'A Dark Psychological Thriller', 13, 10, 540.00, 12.0, 90, 2012, 432, 22,
     'On their fifth wedding anniversary, Amy Dunne disappears; police suspicions quickly turn toward her husband Nick amidst deceit and manipulation.'),
    (86, '978-0307949486', 'The Girl with the Dragon Tattoo', 'Millennium Series: Book 1', 13, 10, 560.00, 10.0, 75, 2005, 480, 25,
     'Journalist Mikael Blomkvist and hacker Lisbeth Salander uncover a dark web of corruption while investigating a 40-year-old family disappearance.'),
    (87, '978-0062073488', 'And Then There Were None', 'The World’s Favorite Agatha Christie Mystery', 6, 10, 440.00, 5.0, 80, 1939, 272, 20,
     'Ten strangers are invited to an isolated island mansion by an absent host, where one by one they are systematically executed according to a rhyme.'),
    (88, '978-0140437867', 'The Hound of the Baskervilles', 'A Sherlock Holmes Adventure', 5, 10, 380.00, 0.0, 85, 1902, 256, 19,
     'Sherlock Holmes and Dr. Watson investigate a terrifying supernatural spectral hound haunting the fog-shrouded moors of Devonshire.'),
    (89, '978-1250301697', 'The Silent Patient', 'A Shocking Psychological Thriller', 16, 10, 510.00, 10.0, 90, 2019, 336, 23,
     'Alicia Berenson shoots her husband five times in the face and never speaks another word; a psychotherapist becomes obsessed with uncovering why.'),
    (90, '978-0062068415', 'Shutter Island', 'A Gripping Mystery of the Mind', 6, 10, 480.00, 10.0, 65, 2003, 400, 24,
     'US Marshal Teddy Daniels investigates the baffling escape of a patient from an island fortress hospital for the criminally insane.'),

    # 91-96: History, Science & Biography
    (91, '978-0062316097', 'Sapiens', 'A Brief History of Humankind', 6, 11, 650.00, 15.0, 120, 2014, 464, 26,
     'Yuval Noah Harari surveys human history from the Cognitive Revolution 70,000 years ago to the biotechnology frontiers of tomorrow.'),
    (92, '978-0062464316', 'Homo Deus', 'A Brief History of Tomorrow', 6, 11, 680.00, 10.0, 85, 2016, 448, 26,
     'Harari explores what will happen when humankind conquers famine, plague, and war, pursuing immortality, bliss, and godlike powers.'),
    (93, '978-0393354324', 'Guns, Germs, and Steel', 'The Fates of Human Societies', 13, 11, 590.00, 10.0, 70, 1997, 528, 27,
     'Jared Diamond explains why Eurasian and North African civilizations survived and conquered other societies based on biogeography and technology.'),
    (94, '978-0767908184', 'A Short History of Nearly Everything', 'From the Big Bang to the Rise of Civilization', 13, 11, 620.00, 12.0, 75, 2003, 544, 28,
     'Bill Bryson’s witty and illuminating chronicle of how the universe evolved from nothing into the complex living planet we inhabit today.'),
    (95, '978-1451648539', 'Steve Jobs', 'The Exclusive Biography', 9, 11, 750.00, 10.0, 90, 2011, 656, 29,
     'Walter Isaacson’s riveting, uncensored biography based on dozens of exclusive interviews with the visionary founder of Apple.'),
    (96, '978-1524763138', 'Becoming', 'An Intimate and Inspiring Memoir', 5, 11, 720.00, 15.0, 105, 2018, 448, 30,
     'Michelle Obama chronicles the experiences that shaped her, from her childhood in Chicago to her years as First Lady of the United States.'),

    # 97-100: Contemporary & Literary Fiction
    (97, '978-1594631931', 'The Kite Runner', 'A Masterpiece of Friendship and Redemption', 5, 12, 490.00, 10.0, 80, 2003, 371, 31,
     'An unforgettable tale of unlikely friendship between a wealthy boy and the son of his father\'s servant amidst turbulent Kabul history.'),
    (98, '978-1594489501', 'A Thousand Splendid Suns', 'A Breathtaking Story of Two Afghan Women', 5, 12, 510.00, 10.0, 85, 2007, 384, 31,
     'Khaled Hosseini chronicles the bond forged between two generations of women brought together by war, loss, and survival in Afghanistan.'),
    (99, '978-0156027328', 'Life of Pi', 'A Story of Faith, Hope, and Survival', 13, 12, 440.00, 5.0, 75, 2001, 319, 32,
     'A sixteen-year-old boy named Pi Patel survives a shipwreck in the Pacific Ocean, marooned on a lifeboat with a ferocious Bengal tiger.'),
    (100, '978-0375842207', 'The Book Thief', 'Narrated by Death in Nazi Germany', 5, 12, 530.00, 12.0, 90, 2005, 552, 33,
     'In 1939 Nazi Germany, young Liesel Meminger finds solace in stealing books and sharing them with her neighbors and hidden Jewish refugee.')
]

def seed_into_cursor(cursor):
    """Generates all 100 SVG covers and populates categories, publishers, authors, books, and reviews."""
    print(f"Generating 100 SVG covers and inserting 100 books...")
    for b in BOOKS:
        b_id = b[0]
        title = b[2]
        sub = b[3]
        cat_id = b[5]
        year = b[9]
        auth_id = b[11]
        author_name = next((a[1] for a in AUTHORS if a[0] == auth_id), 'Author')
        
        svg_content = generate_svg_cover(b_id, title, sub, author_name, cat_id, year)
        cover_path = os.path.join(COVERS_DIR, f'book_{b_id}.svg')
        with open(cover_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    
    # Re-create tables if missing
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        slug TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS publishers (
        publisher_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        country TEXT,
        founded_year INTEGER,
        website TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        author_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        bio TEXT,
        birth_year INTEGER,
        country TEXT
    );
    """)

    cursor.execute("DELETE FROM book_authors")
    cursor.execute("DELETE FROM books")
    cursor.execute("DELETE FROM categories")
    cursor.execute("DELETE FROM publishers")
    cursor.execute("DELETE FROM authors")

    cursor.executemany("INSERT INTO categories (category_id, name, slug, description, icon) VALUES (?, ?, ?, ?, ?)", CATEGORIES)
    cursor.executemany("INSERT INTO publishers (publisher_id, name, country, founded_year, website) VALUES (?, ?, ?, ?, ?)", PUBLISHERS)
    cursor.executemany("INSERT INTO authors (author_id, name, bio, birth_year, country) VALUES (?, ?, ?, ?, ?)", AUTHORS)

    books_insert = []
    book_authors_insert = []
    reviews_insert = []

    review_templates = [
        (5, "Absolute Masterpiece!", "One of the most profound, captivating, and well-written books I have ever read. A must-have for every serious reader."),
        (5, "Highly Recommended", "The depth of insights, clarity of prose, and engaging storytelling make this an undeniable classic."),
        (4, "Fantastic Read", "Thoroughly enjoyable and thought-provoking from beginning to end. Exceptional quality edition."),
        (5, "Exceeded Expectations", "PageVault delivered a beautiful pristine copy. The content itself changed my perspective completely.")
    ]

    for b in BOOKS:
        b_id = b[0]
        isbn = b[1]
        title = b[2]
        subtitle = b[3]
        pub_id = b[4]
        cat_id = b[5]
        price = b[6]
        discount_pct = b[7]
        stock_qty = b[8]
        pub_year = b[9]
        page_count = b[10]
        auth_id = b[11]
        desc = b[12]
        jpg_filename = f"book_{b_id}.jpg"
        if os.path.exists(os.path.join(COVERS_DIR, jpg_filename)):
            cover_image = f"/static/img/covers/{jpg_filename}"
        else:
            cover_image = f"/static/img/covers/book_{b_id}.svg"

        books_insert.append((
            b_id, isbn, title, subtitle, pub_id, cat_id, price, discount_pct,
            stock_qty, pub_year, page_count, 'English', cover_image, desc
        ))

        book_authors_insert.append((b_id, auth_id, 1))

        # 2 sample reviews per book for ratings
        r1 = random.choice(review_templates)
        r2 = random.choice(review_templates)
        reviews_insert.append((b_id, 1, r1[0], r1[1], r1[2]))
        reviews_insert.append((b_id, 2, r2[0], r2[1], r2[2]))

    cursor.executemany("""
    INSERT INTO books (book_id, isbn, title, subtitle, publisher_id, category_id, price, discount_pct, stock_qty, publication_year, page_count, language, cover_image, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, books_insert)

    cursor.executemany("""
    INSERT INTO book_authors (book_id, author_id, is_primary) VALUES (?, ?, ?)
    """, book_authors_insert)

    cursor.execute("DELETE FROM reviews")
    cursor.executemany("""
    INSERT INTO reviews (book_id, user_id, rating, review_title, review_text) VALUES (?, ?, ?, ?, ?)
    """, reviews_insert)

def run(db_path=None):
    target_db = db_path if db_path else os.path.join(BASE_DIR, 'pagevault.db')
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    seed_into_cursor(cursor)
    conn.commit()

    # Verify counts
    cursor.execute("SELECT COUNT(*) FROM books WHERE is_deleted = 0")
    total_b = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM books WHERE is_deleted = 0 AND stock_qty <= 20")
    low_b = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM categories")
    total_c = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM authors")
    total_a = cursor.fetchone()[0]

    conn.close()

    print(f"SUCCESS!")
    print(f"Total Books: {total_b} (Target: 100)")
    print(f"Urgent Low Stock Books (<= 20): {low_b} (Target: exactly 3)")
    print(f"Total Categories: {total_c}")
    print(f"Total Authors: {total_a}")

if __name__ == '__main__':
    run()
