#!/usr/bin/env python3
"""
Performance Testing for JellyRancher v2.0.0 Features

Tests performance of TMDB, episode analysis, and movie analysis features
with simulated large datasets.

Usage:
    python performance_test.py [--episodes N] [--movies N] [--tmdb N]

Options:
    --episodes N    Number of episode files to simulate (default: 1000)
    --movies N      Number of movie files to simulate (default: 500)
    --tmdb N        Number of TMDB searches to simulate (default: 50)
"""

import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Add paths
current_dir = Path(__file__).parent
scripts_dir = current_dir / "scripts"
core_dir = scripts_dir / "core"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(core_dir))
sys.path.insert(0, str(scripts_dir / "_common"))

from episode_title_backend import EpisodeTitleAnalyzer
from movie_name_backend import MovieNameAnalyzer
from tmdb_backend import TMDBBackend
from _common.logger import ProjectLogger


class PerformanceTester:
    """Performance testing for JellyRancher features."""

    def __init__(self):
        self.logger = ProjectLogger("performance_test")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="choco_performance_"))
        self.results = {}

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_tv_show(self, show_name: str, season_count: int = 5, episodes_per_season: int = 20) -> Path:
        """Create a test TV show directory structure."""
        show_dir = self.temp_dir / show_name
        show_dir.mkdir(parents=True, exist_ok=True)

        for season in range(1, season_count + 1):
            season_dir = show_dir / f"Season {season:02d}"
            season_dir.mkdir(exist_ok=True)

            for episode in range(1, episodes_per_season + 1):
                # Create various filename patterns
                patterns = [
                    f"{show_name}.S{season:02d}E{episode:02d}.Episode.Title.mkv",
                    f"{show_name} - S{season:02d}E{episode:02d} - Episode Title.mp4",
                    f"{show_name}.S{season:02d}E{episode:02d}.avi",
                    f"{show_name} S{season:02d}E{episode:02d} Episode Title.m4v"
                ]

                # Add some problematic patterns
                if episode % 10 == 0:  # Every 10th episode has issues
                    patterns = [
                        f"{show_name}.S{season:02d}E{episode:02d}.HDTV.x264-GROUP.mkv",  # Codec in name
                        f"{show_name} S{season:02d}E{episode:02d}.avi",  # Missing title
                        f"{show_name}.S{season:02d}E{episode:02d}.Episode.Title.PROPER.mkv"  # Extra tags
                    ]

                for pattern in patterns[:1]:  # Just create one file per episode
                    episode_file = season_dir / pattern
                    episode_file.write_text("dummy video file")  # Create empty file

        return show_dir

    def create_test_movie_library(self, movie_count: int) -> Path:
        """Create a test movie library."""
        movies_dir = self.temp_dir / "Movies"
        movies_dir.mkdir(parents=True, exist_ok=True)

        movie_titles = [
            "The Shawshank Redemption", "The Godfather", "The Dark Knight", "Pulp Fiction",
            "Forrest Gump", "Inception", "The Matrix", "Goodfellas", "The Silence of the Lambs",
            "Fight Club", "The Lord of the Rings", "Star Wars", "The Avengers", "Titanic",
            "Jurassic Park", "Back to the Future", "Indiana Jones", "Terminator", "Alien",
            "Blade Runner", "The Shining", "Psycho", "Jaws", "E.T.", "Ghostbusters"
        ]

        for i in range(movie_count):
            base_title = movie_titles[i % len(movie_titles)]
            year = 1980 + (i % 40)  # Years from 1980-2019

            # Create various filename patterns, some with issues
            if i % 5 == 0:  # 20% have codec tags
                filename = f"{base_title} ({year}) HDTV x264-GROUP.mkv"
            elif i % 7 == 0:  # ~14% have truncated titles
                filename = f"{base_title[:10]}... ({year}).mp4"
            elif i % 11 == 0:  # ~9% missing year
                filename = f"{base_title}.mkv"
            else:  # Good filenames
                filename = f"{base_title} ({year}).mkv"

            movie_file = movies_dir / filename
            movie_file.write_text("dummy movie file")

        return movies_dir

    def test_episode_analysis(self, show_count: int = 5) -> Dict[str, Any]:
        """Test episode analysis performance."""
        self.logger.info(f"Testing episode analysis with {show_count} shows")

        # Create test shows
        shows = []
        for i in range(show_count):
            show_name = f"TestShow{i:02d}"
            show_dir = self.create_test_tv_show(show_name, season_count=3, episodes_per_season=10)
            shows.append(show_dir)

        analyzer = EpisodeTitleAnalyzer()

        start_time = time.time()
        total_episodes = 0
        total_issues = 0

        for show_dir in shows:
            self.logger.info(f"Analyzing {show_dir.name}...")
            try:
                results = analyzer.analyze_show_folder(show_dir)
                total_episodes += results.get('total_files', 0)
                total_issues += results.get('issues_count', 0)
            except Exception as e:
                self.logger.error(f"Error analyzing {show_dir.name}: {e}")

        end_time = time.time()
        duration = end_time - start_time

        return {
            'operation': 'episode_analysis',
            'shows_analyzed': show_count,
            'total_episodes': total_episodes,
            'total_issues': total_issues,
            'duration_seconds': duration,
            'episodes_per_second': total_episodes / duration if duration > 0 else 0,
            'avg_time_per_show': duration / show_count if show_count > 0 else 0
        }

    def test_movie_analysis(self, movie_count: int) -> Dict[str, Any]:
        """Test movie analysis performance."""
        self.logger.info(f"Testing movie analysis with {movie_count} movies")

        # Create test movie library
        movies_dir = self.create_test_movie_library(movie_count)

        analyzer = MovieNameAnalyzer()

        start_time = time.time()

        def progress_callback(current, total, message):
            if current % 100 == 0:  # Log every 100 movies
                self.logger.info(f"Progress: {current}/{total} - {message}")

        results = analyzer.analyze_movies_folder(str(movies_dir), progress_callback=progress_callback)

        end_time = time.time()
        duration = end_time - start_time

        return {
            'operation': 'movie_analysis',
            'movies_analyzed': movie_count,
            'issues_found': sum(results['summary'].values()),
            'duration_seconds': duration,
            'movies_per_second': movie_count / duration if duration > 0 else 0,
            'summary': results['summary']
        }

    def test_tmdb_searches(self, search_count: int) -> Dict[str, Any]:
        """Test TMDB search performance."""
        self.logger.info(f"Testing TMDB searches with {search_count} queries")

        # Mock TMDB backend since we don't want to hit real API
        class MockTMDBBackend:
            def search_shows(self, query, year=None):
                # Simulate API delay
                time.sleep(0.1)  # 100ms per search
                # Return mock results
                return [{
                    'id': 12345,
                    'name': f"Mock Show for {query}",
                    'first_air_date': f"{1980 + hash(query) % 40}-01-01",
                    'overview': f"Mock overview for {query}"
                }]

        backend = MockTMDBBackend()

        search_terms = [
            "Breaking Bad", "Game of Thrones", "The Office", "Stranger Things",
            "The Mandalorian", "Friends", "The Big Bang Theory", "Black Mirror",
            "Westworld", "Chernobyl", "The Crown", "Narcos", "Money Heist",
            "Dark", "Ozark", "House of Cards", "13 Reasons Why", "Riverdale",
            "The Witcher", "The Umbrella Academy", "Locke & Key", "Lovecraft Country"
        ]

        start_time = time.time()
        successful_searches = 0

        for i in range(search_count):
            query = search_terms[i % len(search_terms)]
            try:
                results = backend.search_shows(query)
                if results:
                    successful_searches += 1
            except Exception as e:
                self.logger.error(f"Search failed for '{query}': {e}")

        end_time = time.time()
        duration = end_time - start_time

        return {
            'operation': 'tmdb_search',
            'searches_attempted': search_count,
            'searches_successful': successful_searches,
            'duration_seconds': duration,
            'searches_per_second': search_count / duration if duration > 0 else 0,
            'avg_time_per_search': duration / search_count if search_count > 0 else 0
        }

    def run_all_tests(self, episodes: int = 1000, movies: int = 500, tmdb_searches: int = 50) -> Dict[str, Any]:
        """Run all performance tests."""
        self.logger.info("Starting JellyRancher v2.0.0 Performance Tests")
        self.logger.info(f"Test parameters: {episodes} episodes, {movies} movies, {tmdb_searches} TMDB searches")

        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'parameters': {
                'episodes': episodes,
                'movies': movies,
                'tmdb_searches': tmdb_searches
            },
            'tests': []
        }

        try:
            # Test episode analysis
            episode_results = self.test_episode_analysis(show_count=max(1, episodes // 150))  # ~150 episodes per show
            results['tests'].append(episode_results)

            # Test movie analysis
            movie_results = self.test_movie_analysis(movies)
            results['tests'].append(movie_results)

            # Test TMDB searches
            tmdb_results = self.test_tmdb_searches(tmdb_searches)
            results['tests'].append(tmdb_results)

        finally:
            self.cleanup()

        # Print summary
        self.print_results(results)
        return results

    def print_results(self, results: Dict[str, Any]):
        """Print performance test results."""
        print("\n" + "="*60)
        print("JELLYRANCHER V2.0.0 PERFORMANCE TEST RESULTS")
        print("="*60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Parameters: {results['parameters']}")
        print()

        for test in results['tests']:
            print(f"📊 {test['operation'].replace('_', ' ').title()}")
            print("-" * 40)

            if test['operation'] == 'episode_analysis':
                print(".2f")
                print(f"  Episodes analyzed: {test['total_episodes']}")
                print(f"  Issues found: {test['total_issues']}")
                print(".2f")
                print(".2f")

            elif test['operation'] == 'movie_analysis':
                print(".2f")
                print(f"  Issues found: {test['issues_found']}")
                print(".2f")
                print(f"  Issue breakdown: {test['summary']}")

            elif test['operation'] == 'tmdb_search':
                print(".2f")
                print(f"  Successful searches: {test['searches_successful']}/{test['searches_attempted']}")
                print(".2f")
                print(".2f")

            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="JellyRancher v2.0.0 Performance Testing")
    parser.add_argument('--episodes', type=int, default=1000,
                       help='Number of episode files to simulate (default: 1000)')
    parser.add_argument('--movies', type=int, default=500,
                       help='Number of movie files to simulate (default: 500)')
    parser.add_argument('--tmdb', type=int, default=50,
                       help='Number of TMDB searches to simulate (default: 50)')

    args = parser.parse_args()

    tester = PerformanceTester()
    try:
        results = tester.run_all_tests(
            episodes=args.episodes,
            movies=args.movies,
            tmdb_searches=args.tmdb
        )

        # Save results to file
        output_file = Path("performance_results.json")
        import json
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"📄 Detailed results saved to {output_file}")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())