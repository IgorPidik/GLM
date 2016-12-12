__author__ = 'igor'


class GLM(object):
    def __init__(self, vFilePath):
        vFile = open(vFilePath)
        self.v = {}
        if not vFile:
            print "error openning file"
        for l in vFile:
            key, val = l.strip().split()
            self.v[key] = float(val)
        vFile.close()

    def productVG(self, g):
        return sum((self.getV(key) * 1 for key in g))

    def getV(self, key):
        return self.v.get(key, 0)

    def getF(self, sentence, tags):
        f = {}

        def getTag(tags, i):
            if i < 0:
                return "*"
            else:
                return tags[i]

        for n in range(0, len(sentence)):
            g = self.getG(getTag(tags, n - 2), getTag(tags, n - 1), getTag(tags, n), sentence, n)
            for key in g:
                f[key] = f.get(key, 0) + 1

        return f

    def getG(self, s, u, v, sentence, position):

        def gTrigram(s, u, v):
            return ["TRIGRAM:" + s + ":" + u + ":" + v]

        if v == "STOP":
            return gTrigram(s, u, v)

        x = sentence[position]

        def gTag(t, x):
            return ["TAG:" + x + ":" + t]

        def suffix(w, j):
            if j > len(w):
                return w
            else:
                return w[-j:]

        def gSuffix(w, startPoint, endPoint, t):
            for j in range(startPoint, endPoint + 1):
                yield ["SUFFIX:" + suffix(w, j) + ":" + str(j) + ":" + t]

        g = gTrigram(s, u, v) + gTag(v, x)
        for item in gSuffix(x, 1, 3, v):
            g = g + item

        return g

    def argmax(self, ls):
        return max(ls, key=lambda x: x[1])

    def viterbiGLM(self, sentence):

        def getPossibleTag(i):
            if i < 1:
                return ["*"]
            else:
                return ["O", "I-GENE"]

        n = len(sentence)
        sentence = [""] + sentence
        y = [""] * (n + 1)
        pi = {}
        bp = {}

        pi[0, "*", "*"] = 0

        for k in range(1, n + 1):
            for u in getPossibleTag(k - 1):
                for s in getPossibleTag(k):
                    bp[k, u, s], pi[k, u, s] = self.argmax(
                        [(t, (pi[k - 1, t, u] + self.productVG(self.getG(t, u, s, sentence, k)))) for t in
                         getPossibleTag(k - 2)])
        (y[n - 1], y[n]), score = self.argmax(
            [((u, s), pi[n, u, s] + self.productVG(self.getG(u, s, "STOP", sentence, n + 1))) for u in
             getPossibleTag(n - 1) for s in getPossibleTag(n)])

        for k in range(n - 2, 0, -1):
            y[k] = bp[k + 2, y[k + 1], y[k + 2]]
        y[0] = "*"
        return y[1:n + 1]

    def perceptronAlgorithm(self, trainingFilePath, outFile):
        wordSequences, tagSequences = self.getWordTagSequences(trainingFilePath)
        self.v = {}
        numIteration = 6
        for t in range(0, numIteration):
            print ("iteration:", t)
            for i in range(0, len(wordSequences)):
                x = wordSequences[i]
                y = tagSequences[i]
                bestF = self.getF(x, self.viterbiGLM(x))
                goldF = self.getF(x, y)
                for key, val in goldF.iteritems():
                    self.v[key] = self.v.get(key, 0) + (val - bestF.get(key, 0))
                for key, val in bestF.iteritems():
                    self.v[key] = self.v.get(key, 0) + (goldF.get(key, 0) - val)
        out = open(outFile, 'w')
        for key, val in self.v.iteritems():
            out.write(key + " " + str(val) + '\n')
        out.flush()
        out.close()

    def getWordTagSequences(self, trainingFilePath):
        trainingFile = open(trainingFilePath)
        if not trainingFile:
            print "getWordTagSequence: file error"
        wordSequence = []
        tagSequence = []

        words = []
        tags = []
        for l in trainingFile:
            if l == '\n':
                wordSequence.append(words)
                tagSequence.append(tags)
                words = []
                tags = []
            else:
                word, tag = l.strip().split()
                words.append(word)
                tags.append(tag)

        trainingFile.close()
        return wordSequence, tagSequence


def tagFile(glm, inputFile, outputFile):
    instream = open(inputFile, 'r')
    outstream = open(outputFile, 'w')

    sentence = []
    for l in instream:
        if l == '\n':
            tagSequence = glm.viterbiGLM(sentence)
            for i in range(0, len(sentence)):
                outstream.write(sentence[i] + " " + tagSequence[i] + "\n")
            outstream.write("\n")
            sentence = []
        else:
            sentence.append(l.strip())
    instream.close()
    outstream.flush()
    outstream.close()


def main():
    glm = GLM("../data/suffix.model")

    tagFile(glm, "../data/gene.dev", "../data/gene_dev.p1.out")

    # glm.perceptronAlgorithm("../data/gene.train", "../data/suffix.model")

    # tagFile(glm, "../data/gene.dev", "../data/gene_dev.p1.out")


main()
