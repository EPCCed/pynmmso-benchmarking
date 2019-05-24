import multiprocessing

import run


def main():

    jobs = []
    for j in range(1, 21):

        process = multiprocessing.Process(target=run.NmmsoRunner, args=(j, True))
        jobs.append(process)
        process.start()


if __name__ == "__main__":
    main()
