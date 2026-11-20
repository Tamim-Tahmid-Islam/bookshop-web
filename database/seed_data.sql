-- =============================================================================
-- PageVault - Sample Seed Data
-- =============================================================================
USE pagevault_db;

-- 1. Insert Categories
INSERT INTO categories (category_id, name, slug, description, icon) VALUES
(1, 'Database & Systems', 'database-systems', 'Relational models, SQL optimization, index structures and distributed databases.', 'database'),
(2, 'Computer Science & Software', 'computer-science', 'Algorithms, system design, clean architecture, and computing principles.', 'cpu'),
(3, 'Fantasy & Adventure', 'fantasy-adventure', 'Magical universes, epic sagas, heroic quests, and legendary chronicles.', 'sparkles'),
(4, 'Self-Help & Personal Growth', 'self-help', 'Productivity, habit engineering, mental toughness, and behavioral psychology.', 'zap'),
(5, 'Classic Drama & Poetry', 'classic-drama', 'Timeless theatrical tragedies, comedies, historical plays, and verse.', 'book-open'),
(6, 'Inspirational Fiction', 'inspirational-fiction', 'Philosophical allegories, spiritual voyages, and transformative tales.', 'compass'),
(7, 'Science Fiction & Dystopia', 'science-fiction', 'Futuristic speculative universes, political dystopias, and space operas.', 'rocket'),
(8, 'Finance & Behavioral Economics', 'finance-economics', 'Wealth building, rational decision making, and cognitive bias analysis.', 'trending-up'),
(9, 'Artificial Intelligence', 'artificial-intelligence', 'Machine learning, neural networks, intelligent agents, and reasoning.', 'brain');

-- 2. Insert Publishers
INSERT INTO publishers (publisher_id, name, country, founded_year, website) VALUES
(1, 'Addison-Wesley Professional', 'USA', 1942, 'https://www.pearson.com'),
(2, 'O''Reilly Media', 'USA', 1978, 'https://www.oreilly.com'),
(3, 'The MIT Press', 'USA', 1962, 'https://mitpress.mit.edu'),
(4, 'Morgan Kaufmann Publishers', 'USA', 1984, 'https://www.elsevier.com'),
(5, 'Penguin Random House', 'USA', 1927, 'https://www.penguinrandomhouse.com'),
(6, 'Oxford University Press', 'UK', 1586, 'https://global.oup.com'),
(7, 'HarperCollins Publishers', 'USA', 1817, 'https://www.harpercollins.com'),
(8, 'Bloomsbury Publishing', 'UK', 1986, 'https://www.bloomsbury.com'),
(9, 'Scholastic Inc.', 'USA', 1920, 'https://www.scholastic.com'),
(10, 'Simon & Schuster (Folger)', 'USA', 1924, 'https://www.simonandschuster.com'),
(11, 'Avery (Penguin Group)', 'USA', 1976, 'https://www.penguin.com'),
(12, 'Grand Central Publishing', 'USA', 1970, 'https://www.hachettebookgroup.com'),
(13, 'Lioncrest Publishing', 'USA', 2017, 'https://www.lioncrest.com'),
(14, 'Harriman House', 'UK', 1992, 'https://harriman-house.com');

-- 3. Insert Authors
INSERT INTO authors (author_id, name, bio, birth_year, country) VALUES
(1, 'Abraham Silberschatz', 'Professor of Computer Science at Yale University; renowned author of fundamental database textbooks.', 1947, 'USA'),
(2, 'Henry F. Korth', 'Professor of Computer Science and Engineering at Lehigh University; pioneer in database systems.', 1956, 'USA'),
(3, 'S. Sudarshan', 'Subrao M. Nilekani Chair Professor at IIT Bombay; expert in query optimization and database storage.', 1964, 'India'),
(4, 'Martin Kleppmann', 'Researcher in distributed systems at University of Cambridge; author of Designing Data-Intensive Applications.', 1982, 'UK'),
(5, 'Donald E. Knuth', 'Professor Emeritus at Stanford University; father of algorithm analysis and creator of TeX.', 1938, 'USA'),
(6, 'Martin Fowler', 'Chief Scientist at ThoughtWorks; authority on refactoring and software architecture.', 1963, 'UK'),
(7, 'Robert C. Martin', 'Co-author of the Agile Manifesto; widely known as Uncle Bob for Clean Code series.', 1952, 'USA'),
(8, 'Stuart Russell', 'Professor of Computer Science at UC Berkeley; AI pioneer and author of the leading AI textbook.', 1962, 'UK'),
(9, 'Peter Norvig', 'Director of Research at Google; former NASA lead and eminent computer scientist.', 1956, 'USA'),
(10, 'Frank Herbert', 'American science fiction author best known for the epic Dune saga.', 1920, 'USA'),
(11, 'George Orwell', 'English novelist and essayist whose work is characterised by lucid prose and social criticism.', 1903, 'UK'),
(12, 'Daniel Kahneman', 'Nobel laureate in Economics and pioneer of behavioral psychology.', 1934, 'Israel'),
(13, 'Thomas H. Cormen', 'Emeritus Professor of Computer Science at Dartmouth College and co-author of CLRS.', 1956, 'USA'),
(14, 'C.J. Date', 'Independent author and researcher specializing in the relational database model.', 1938, 'UK'),
(15, 'J.K. Rowling', 'British author celebrated for creating the world of Harry Potter, inspiring generations of readers.', 1965, 'UK'),
(16, 'Paulo Coelho', 'Acclaimed Brazilian novelist whose philosophical allegories have sold over 320 million copies worldwide.', 1947, 'Brazil'),
(17, 'William Shakespeare', 'Legendary English playwright, poet, and actor widely regarded as the greatest dramatist of world literature.', 1564, 'UK'),
(18, 'James Clear', 'Renowned behavioral researcher, speaker, and author of the record-breaking bestseller Atomic Habits.', 1986, 'USA'),
(19, 'Mark Manson', 'Self-help author and blogger known for pragmatic, no-nonsense approaches to modern personal development.', 1984, 'USA'),
(20, 'Cal Newport', 'Associate Professor of Computer Science at Georgetown University and advocate of digital focus.', 1982, 'USA'),
(21, 'David Goggins', 'Retired Navy SEAL, ultramarathon runner, and author advocating peak mental discipline.', 1975, 'USA'),
(22, 'Morgan Housel', 'Partner at Collaborative Fund and bestselling author on behavioral finance and psychology.', 1984, 'USA');

-- 4. Insert Books (Prices in BDT)
INSERT INTO books (book_id, isbn, title, subtitle, publisher_id, category_id, price, discount_pct, stock_qty, publication_year, page_count, language, cover_image, description) VALUES
(1, '978-0078022159', 'Database System Concepts', 'Seventh Edition', 4, 1, 1250.00, 10.00, 42, 2019, 1376, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1348180424i/18579.jpg', 'Comprehensive coverage of database management concepts, relational models, SQL query processing, index architectures, concurrency control, and ACID transactions.'),
(2, '978-1449373320', 'Designing Data-Intensive Applications', 'The Big Ideas Behind Reliable Systems', 2, 1, 950.00, 15.00, 75, 2017, 616, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1453982827i/23463279.jpg', 'Key insights into database storage engines, B-trees, LSM-trees, replication, partitioning, distributed transactions, and stream processing.'),
(3, '978-0134494166', 'Clean Architecture', 'A Craftsman''s Guide to Software Structure', 1, 2, 650.00, 5.00, 58, 2017, 432, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1495947702i/18043011.jpg', 'Essential architectural rules for creating clean software systems with decoupled database layers, business domain boundaries, and testable frameworks.'),
(4, '978-0262033848', 'Introduction to Algorithms (CLRS)', 'Fourth Edition', 3, 2, 1450.00, 12.00, 31, 2022, 1312, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1387741681i/108986.jpg', 'The standard worldwide guide to algorithms: dynamic programming, graph traversal, greedy heuristics, B-trees, sorting algorithms, and complexity analysis.'),
(5, '978-0134610993', 'Artificial Intelligence: A Modern Approach', 'Fourth Edition', 1, 9, 1600.00, 8.00, 24, 2020, 1168, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1347649539i/72005.jpg', 'The most authoritative introduction to artificial intelligence, covering rational agents, probabilistic reasoning, reinforcement learning, and neural architectures.'),
(6, '978-0441013593', 'Dune', 'The Epic Science Fiction Masterpiece', 5, 7, 550.00, 20.00, 110, 1965, 896, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1555447414i/44767458.jpg', 'Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides, who inherits a vast planetary destiny amidst geopolitical and ecological conflict.'),
(7, '978-0451524935', '1984', 'A Dystopian Classic', 5, 7, 350.00, 0.00, 85, 1949, 328, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1657781256i/61439040.jpg', 'Winston Smith toes the Party line, rewriting history to satisfy the Ministry of Truth, while harboring forbidden thoughts in an all-seeing totalitarian state.'),
(8, '978-0374533557', 'Thinking, Fast and Slow', 'Cognitive Biases and Decision Systems', 7, 8, 580.00, 10.00, 64, 2011, 512, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1317793965i/11468377.jpg', 'Exploration of two modes of thought: System 1 (fast, intuitive, emotional) and System 2 (slower, deliberate, logical) and how they shape judgments.'),
(9, '978-0201633610', 'Design Patterns: Elements of Reusable Software', 'Classic Gang of Four', 1, 2, 750.00, 15.00, 39, 1994, 416, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1348027904i/85009.jpg', 'The canonical catalog of 23 classic software design patterns categorized into Creational, Structural, and Behavioral solutions.'),
(10, '978-0321127426', 'Patterns of Enterprise Application Architecture', 'Data Mapping and Domain Models', 1, 2, 850.00, 5.00, 29, 2002, 560, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1440319405i/70156.jpg', 'Detailed patterns for mapping object-oriented models to relational database tables, managing transactions, unit of work, and domain logic layers.'),
(11, '978-0321392794', 'An Introduction to Database Systems', 'Eighth Edition', 1, 1, 1100.00, 10.00, 18, 2003, 1024, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1388188169i/66826.jpg', 'The foundational theoretical text on the relational model, relational algebra, tuple calculus, normalization theory, and integrity constraints by C.J. Date.'),
(12, '978-0321751041', 'The Art of Computer Programming, Vol 1', 'Fundamental Algorithms', 1, 2, 1350.00, 0.00, 15, 1997, 672, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1348630043i/112239.jpg', 'Knuth''s monumental multi-volume work providing exact mathematical analyses of algorithm structures and memory representations.'),
(13, '978-0590353427', 'Harry Potter and the Sorcerer''s Stone', 'Book 1 of the Hogwarts Series', 9, 3, 620.00, 10.00, 95, 1997, 309, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474154022i/3.jpg', 'Harry Potter has never even heard of Hogwarts when letters start dropping on the doormat. On his eleventh birthday, he discovers he is a wizard destined for an extraordinary magical world.'),
(14, '978-0439064873', 'Harry Potter and the Chamber of Secrets', 'Book 2 of the Hogwarts Series', 9, 3, 650.00, 10.00, 80, 1998, 341, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474169725i/15881.jpg', 'The Dursleys were so mean that all Harry wanted was to return to Hogwarts. But a sinister house-elf warns of great danger, and mysterious petrifications begin within the castle walls.'),
(15, '978-0439136365', 'Harry Potter and the Prisoner of Azkaban', 'Book 3 of the Hogwarts Series', 9, 3, 680.00, 12.00, 88, 1999, 435, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1630547330i/5.jpg', 'For twelve long years, the dread fortress of Azkaban held an infamous prisoner named Sirius Black. Now he has escaped, and the Dementors patrol Hogwarts looking for him.'),
(16, '978-0439139601', 'Harry Potter and the Goblet of Fire', 'Book 4 of the Hogwarts Series', 9, 3, 750.00, 15.00, 72, 2000, 734, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1554006152i/6.jpg', 'Harry wants to get away from the pernicious Dursleys and attend the Quidditch World Cup. Little does he know that the Triwizard Tournament will demand supreme courage in the face of Lord Voldemort''s return.'),
(17, '978-0062315007', 'The Alchemist', 'A Fable About Following Your Dream', 7, 6, 380.00, 10.00, 120, 1988, 208, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1654371463i/18144590.jpg', 'Santiago, an Andalusian shepherd boy, yearns to travel in search of worldly treasure. His quest will lead him to riches far different and far more satisfying than he ever imagined as he listens to his heart.'),
(18, '978-0061578953', 'Brida', 'A Novel of Magic and Mystery', 7, 6, 420.00, 5.00, 65, 1990, 288, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1388195861i/2984534.jpg', 'The captivating story of Brida, a young Irish girl, and her quest for knowledge, wisdom, and love through ancient spiritual traditions and discovery of her destiny.'),
(19, '978-0061735257', 'The Winner Stands Alone', 'Ambition, Fame and the Superclass', 7, 6, 450.00, 10.00, 48, 2008, 400, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1327918341i/4996985.jpg', 'Set amidst the glamorous backdrop of the Cannes Film Festival, a gripping examination of deep ambition, celebrity culture, and the price of success.'),
(20, '978-0743477123', 'Hamlet, Prince of Denmark', 'The Folger Shakespeare Library', 10, 5, 320.00, 0.00, 90, 1603, 342, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1351051608i/1420.jpg', 'The supreme masterpiece of world drama: Prince Hamlet mourns his murdered father, facing moral paralysis, revenge, feigned madness, and profound existential questions.'),
(21, '978-0743477109', 'Macbeth', 'Tragedy of Ambition and Fate', 10, 5, 300.00, 0.00, 85, 1606, 240, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1459795224i/8852.jpg', 'Spurred by three supernatural witches and his ruthless wife, Scottish general Macbeth commits regicide to seize the throne, descending into paranoia and blood-soaked tyranny.'),
(22, '978-0743477116', 'Romeo and Juliet', 'The Definitive Folger Edition', 10, 5, 290.00, 0.00, 95, 1597, 281, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1631587327i/18135.jpg', 'The timeless tale of star-crossed lovers in Verona whose passionate romance defies the bitter, violent blood-feud between the Montagues and Capulets.'),
(23, '978-0735211292', 'Atomic Habits', 'Tiny Changes, Remarkable Results', 11, 4, 550.00, 15.00, 140, 2018, 320, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1655988385i/40121378.jpg', 'No matter your goals, Atomic Habits offers a proven framework for improving every day. James Clear reveals practical strategies for building good habits, breaking bad ones, and mastering tiny behaviors.'),
(24, '978-0062457714', 'The Subtle Art of Not Giving a F*ck', 'A Counterintuitive Approach to Living a Good Life', 7, 4, 480.00, 10.00, 115, 2016, 224, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1465248106i/28257707.jpg', 'In this generation-defining self-help guide, superstar blogger Mark Manson cuts through the crap to show us how to stop trying to be positive all the time and instead become truly resilient.'),
(25, '978-1455586691', 'Deep Work', 'Rules for Focused Success in a Distracted World', 12, 4, 520.00, 10.00, 85, 2016, 304, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1447957962i/25744928.jpg', 'Deep work is the ability to focus without distraction on a cognitively demanding task. Cal Newport presents an indispensable framework to master complicated information and produce better results in less time.'),
(26, '978-1544512280', 'Can''t Hurt Me', 'Master Your Mind and Defy the Odds', 13, 4, 590.00, 12.00, 90, 2018, 364, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1547846505i/41721428.jpg', 'For David Goggins, childhood was a nightmare of poverty and physical abuse. Through self-discipline, mental toughness, and hard work, he transformed himself into one of the world''s toughest endurance athletes.'),
(27, '978-0857197689', 'The Psychology of Money', 'Timeless Lessons on Wealth, Greed, and Happiness', 14, 8, 540.00, 10.00, 130, 2020, 252, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1581527774i/41881472.jpg', 'Doing well with money isn''t necessarily about what you know. It''s about how you behave. Morgan Housel shares 19 short stories exploring the strange ways people think about money.');

-- 5. Insert Book-Author Relationships (M:N)
INSERT INTO book_authors (book_id, author_id, is_primary) VALUES
(1, 1, TRUE), (1, 2, FALSE), (1, 3, FALSE),
(2, 4, TRUE),
(3, 7, TRUE),
(4, 13, TRUE),
(5, 8, TRUE), (5, 9, FALSE),
(6, 10, TRUE),
(7, 11, TRUE),
(8, 12, TRUE),
(9, 6, FALSE),
(10, 6, TRUE),
(11, 14, TRUE),
(12, 5, TRUE),
(13, 15, TRUE), -- HP 1
(14, 15, TRUE), -- HP 2
(15, 15, TRUE), -- HP 3
(16, 15, TRUE), -- HP 4
(17, 16, TRUE), -- Alchemist
(18, 16, TRUE), -- Brida
(19, 16, TRUE), -- Winner Stands Alone
(20, 17, TRUE), -- Hamlet
(21, 17, TRUE), -- Macbeth
(22, 17, TRUE), -- Romeo & Juliet
(23, 18, TRUE), -- Atomic Habits
(24, 19, TRUE), -- Subtle Art
(25, 20, TRUE), -- Deep Work
(26, 21, TRUE), -- Can't Hurt Me
(27, 22, TRUE); -- Psychology of Money

-- 6. Insert Users
INSERT INTO users (user_id, username, email, password_hash, full_name, role, status) VALUES
(1, 'demo_staff', 'staff@pagevault.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Sarah Jenkins', 'Customer', 'Active'),
(2, 'alex_reader', 'alex@example.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Alex Morgan', 'Customer', 'Active'),
(3, 'sophia_code', 'sophia@tech.edu', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Sophia Chen', 'Customer', 'Active'),
(4, 'tamim_tahmid', 'tamimtahmid270@gmail.com', 'e1fbba4563c9966662a00f863a894dc4439bc480185a6ee4d98f14b2aaea4d87', 'Tamim Tahmid', 'Admin', 'Active');

-- 7. Insert Sample Password Reset Request
INSERT INTO password_resets (user_id, reset_token, reset_code, expires_at, is_used) VALUES
(3, 'demo-token-alex-987654321', '849201', DATE_ADD(NOW(), INTERVAL 1 HOUR), FALSE);

-- 8. Insert Sample Reviews
INSERT INTO reviews (book_id, user_id, rating, review_title, review_text) VALUES
(1, 3, 5, 'Indispensable guide for any DBMS student', 'The depth of explanation on query optimization, B-tree indexes, and serializability is unmatched.'),
(1, 4, 5, 'Clear SQL and Transaction internals', 'The examples on concurrency anomalies and two-phase locking clarified concepts I struggled with.'),
(2, 3, 5, 'Modern Bible of distributed storage', 'Martin Kleppmann bridges theoretical database papers and real-world architectures seamlessly.'),
(4, 3, 5, 'The ultimate algorithmic reference', 'Rigorous, beautiful mathematical proofs and algorithm analysis.'),
(13, 3, 5, 'Pure childhood nostalgia and magic', 'The beginning of the greatest fantasy adventure ever written. Absolutely loved re-reading it!'),
(14, 4, 5, 'Thrilling mystery at Hogwarts', 'The Basilisk mystery and Tom Riddle lore make this one of the most engaging books.'),
(15, 3, 5, 'Best Harry Potter book hands down', 'The Marauders backstory, Sirius Black, and the Time-Turner plot are perfection.'),
(17, 3, 5, 'Life-changing philosophical journey', 'A masterpiece on pursuing your personal legend. Every sentence feels like poetry.'),
(18, 4, 4, 'Mystical and beautifully written', 'Paulo Coelho once again weaves wisdom, spirituality, and human nature into an inspiring tale.'),
(20, 4, 5, 'The pinnacle of dramatic literature', 'Hamlet''s soliloquies on life, death, and human weakness remain breathtaking.'),
(21, 3, 5, 'Chilling psychological tragedy', 'Macbeth''s rapid descent into ambition and madness is Shakespeare at his sharpest.'),
(23, 3, 5, 'Practical, actionable habit building', 'Atomic Habits changed my daily routine completely. The 1% better every day rule actually works!'),
(24, 4, 5, 'Refreshing and honest', 'Mark Manson cuts straight to the core of what actually matters in life.'),
(25, 3, 5, 'Essential reading in the age of distraction', 'Cal Newport proves why focused, uninterrupted cognitive work is the ultimate superpower.'),
(26, 4, 5, 'Unstoppable mindset', 'David Goggins shows that the human mind can overcome any obstacle when you stop making excuses.'),
(27, 3, 5, 'Brilliant take on wealth and human behavior', 'Morgan Housel explains money not as spreadsheet math, but as emotional discipline.');
